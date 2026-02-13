import logging
from datetime import datetime, timedelta

from flask import request
from flask_login import current_user, login_required
from flask_restful import Resource
from sqlalchemy import and_

from tab_view import limiter
from tab_view.models import Device, Event, EventMedia, Media, db
from tab_view.utils import error_response

logger = logging.getLogger(__name__)


class EventResource(Resource):
    """
    REST API for event management
    """

    @login_required
    @limiter.limit("200 per hour")
    def get(self, event_id=None):
        """
        GET /api/v1/events/ - List of events
        GET /api/v1/events/<id> - Single event
        """
        try:
            # Single event
            if event_id:
                event = Event.query.get(event_id)
                if not event:
                    return error_response(f"Event with id {event_id} not found", 404)
                return event.to_dict(), 200

            # List of events with filtering
            device_id = request.args.get("device_id", type=int)
            start_param = request.args.get("start")
            end_param = request.args.get("end")

            # Default range: current month
            if not start_param or not end_param:
                today = datetime.now()
                start_of_month = today.replace(
                    day=1, hour=0, minute=0, second=0, microsecond=0
                )

                # The last day of the month
                if today.month == 12:
                    end_of_month = today.replace(
                        year=today.year + 1, month=1, day=1
                    ) - timedelta(days=1)
                else:
                    end_of_month = today.replace(
                        month=today.month + 1, day=1
                    ) - timedelta(days=1)
                end_of_month = end_of_month.replace(hour=23, minute=59, second=59)
            else:
                try:
                    start_of_month = datetime.fromisoformat(
                        start_param.replace("Z", "")
                    )
                    end_of_month = datetime.fromisoformat(end_param.replace("Z", ""))
                except (ValueError, AttributeError) as e:
                    logger.error(f"Date parsing error in GET /events: {e}")
                    return error_response(
                        "Invalid date format. Use ISO 8601 format.", 400
                    )

            query = Event.query

            if device_id:
                if not Device.query.get(device_id):
                    return error_response(f"Device with id {device_id} not found", 404)
                query = query.filter(Event.device_id == device_id)

            query = query.filter(
                and_(Event.start_time <= end_of_month, Event.end_time >= start_of_month)
            )

            query = query.order_by(Event.start_time.asc())

            events = query.all()
            result = [event.to_dict() for event in events]

            return result, 200

        except Exception as e:
            logger.error(f"Error in GET /events: {e}", exc_info=True)
            return error_response("Internal server error", 500)

    @login_required
    @limiter.limit("200 per hour")
    def post(self):
        """
        POST /api/v1/events/ - Create new event
        """
        try:
            data = request.get_json()

            if not data:
                return error_response("Request body must be JSON", 400)

            required_fields = [
                "title",
                "start_time",
                "end_time",
                "device_id",
                "media_playlist",
            ]
            missing_fields = [field for field in required_fields if not data.get(field)]

            if missing_fields:
                return error_response(
                    f"Missing required fields: {', '.join(missing_fields)}", 400
                )

            if not isinstance(data["title"], str) or len(data["title"].strip()) == 0:
                return error_response("Title must be a non-empty string", 400)

            if len(data["title"]) > 50:
                return error_response("Title is too long (max 50 characters)", 400)

            if (
                not isinstance(data["media_playlist"], list)
                or len(data["media_playlist"]) == 0
            ):
                return error_response("Playlist must be a non-empty array", 400)

            device = Device.query.get(data["device_id"])
            if not device:
                return error_response(
                    f"Device with id {data['device_id']} not found", 404
                )

            try:
                start_time = datetime.fromisoformat(data["start_time"].replace("Z", ""))
                end_time = datetime.fromisoformat(data["end_time"].replace("Z", ""))
            except (ValueError, AttributeError):
                return error_response("Invalid date format. Use ISO 8601 format.", 400)

            if start_time >= end_time:
                return error_response("End time must be after start time", 400)

            # Check overlapping
            overlapping = Event.query.filter(
                Event.device_id == data["device_id"],
                Event.start_time < end_time,
                Event.end_time > start_time,
            ).first()

            if overlapping:
                logger.warning(
                    f"Event creation blocked - Overlap detected for Device \
                        {data['device_id']}: "
                    f"'{overlapping.title}' (User: {current_user.id})"
                )
                return error_response(
                    f'This schedule overlaps with existing event "{overlapping.title}"',
                    409,
                )

            # Create event
            new_event = Event(
                title=data["title"].strip(),
                start_time=start_time,
                end_time=end_time,
                device_id=data["device_id"],
                color=data.get("color", "#3788d8"),
            )
            db.session.add(new_event)
            db.session.flush()

            # Add playlist
            for idx, item in enumerate(data["media_playlist"]):
                if not isinstance(item, dict):
                    db.session.rollback()
                    return error_response(f"Playlist item {idx} must be an object", 400)

                if "media_id" not in item:
                    db.session.rollback()
                    return error_response(f"Playlist item {idx} missing media_id", 400)

                media = Media.query.get(item["media_id"])
                if not media:
                    db.session.rollback()
                    return error_response(
                        f"Media with id {item['media_id']} not found", 404
                    )

                duration = item.get("duration", 10)
                if not isinstance(duration, int) or duration < 1 or duration > 300:
                    duration = 10

                event_media = EventMedia(
                    event_id=new_event.id,
                    media_id=item["media_id"],
                    order=item.get("order", idx),
                    duration=duration,
                )
                db.session.add(event_media)

            db.session.commit()

            logger.info(
                f"Event created: '{new_event.title}' (ID: {new_event.id}) "
                f"for Device {data['device_id']} by User {current_user.id}"
            )

            return {
                "message": "Event created successfully",
                "event": new_event.to_dict(),
            }, 201

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error in POST /events: {e}", exc_info=True)
            return error_response("Internal server error", 500)

    @login_required
    @limiter.limit("200 per hour")
    def put(self, event_id):
        """
        PUT /api/v1/events/<id> - Update event
        """
        try:
            event = Event.query.get(event_id)
            if not event:
                return error_response(f"Event with id {event_id} not found", 404)

            data = request.get_json()
            if not data:
                return error_response("Request body must be JSON", 400)

            # Update title
            if "title" in data:
                if (
                    not isinstance(data["title"], str)
                    or len(data["title"].strip()) == 0
                ):
                    return error_response("Title must be a non-empty string", 400)
                if len(data["title"]) > 50:
                    return error_response("Title is too long (max 50 characters)", 400)
                event.title = data["title"].strip()

            # Update dates
            if "start_time" in data:
                try:
                    event.start_time = datetime.fromisoformat(
                        data["start_time"].replace("Z", "")
                    )
                except (ValueError, AttributeError):
                    return error_response("Invalid start_time format", 400)

            if "end_time" in data:
                try:
                    event.end_time = datetime.fromisoformat(
                        data["end_time"].replace("Z", "")
                    )
                except (ValueError, AttributeError):
                    return error_response("Invalid end_time format", 400)

            if event.start_time >= event.end_time:
                return error_response("End time must be after start time", 400)

            # Check overlapping
            overlapping = Event.query.filter(
                Event.device_id == event.device_id,
                Event.id != event.id,
                Event.start_time < event.end_time,
                Event.end_time > event.start_time,
            ).first()

            if overlapping:
                logger.warning(
                    f"Event update blocked - Overlap detected for \
                        Device {event.device_id}: "
                    f"'{overlapping.title}' (User: {current_user.id})"
                )
                return error_response(
                    f'This schedule overlaps with \
                        existing event "{overlapping.title}"',
                    409,
                )

            # Update color
            if "color" in data:
                color = data["color"]
                if isinstance(color, str) and color.startswith("#") and len(color) == 7:
                    event.color = color

            # Update playlist
            if "media_playlist" in data:
                if not isinstance(data["media_playlist"], list):
                    return error_response("Playlist must be an array", 400)

                if len(data["media_playlist"]) == 0:
                    return error_response("Playlist cannot be empty", 400)

                EventMedia.query.filter_by(event_id=event.id).delete()

                for idx, item in enumerate(data["media_playlist"]):
                    if not isinstance(item, dict):
                        db.session.rollback()
                        return error_response(
                            f"Playlist item {idx} must be an object", 400
                        )

                    if "media_id" not in item:
                        db.session.rollback()
                        return error_response(
                            f"Playlist item {idx} missing media_id", 400
                        )

                    media = Media.query.get(item["media_id"])
                    if not media:
                        db.session.rollback()
                        return error_response(
                            f"Media with id {item['media_id']} not found", 404
                        )

                    duration = item.get("duration", 10)
                    if not isinstance(duration, int) or duration < 1 or duration > 300:
                        duration = 10

                    event_media = EventMedia(
                        event_id=event.id,
                        media_id=item["media_id"],
                        order=item.get("order", idx),
                        duration=duration,
                    )
                    db.session.add(event_media)

            db.session.commit()

            logger.info(
                f"Event updated: '{event.title}' (ID: {event.id}) "
                f"by User {current_user.id}"
            )

            return {
                "message": "Event updated successfully",
                "event": event.to_dict(),
            }, 200

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error in PUT /events/{event_id}: {e}", exc_info=True)
            return error_response("Internal server error", 500)

    @login_required
    @limiter.limit("200 per hour")
    def delete(self, event_id):
        """
        DELETE /api/v1/events/<id> - Delete event
        """
        try:
            event = Event.query.get(event_id)
            if not event:
                return error_response(
                    f"Event with id {event_id} \
                                      not found",
                    404,
                )

            event_title = event.title
            event_id_val = event.id

            db.session.delete(event)
            db.session.commit()

            logger.info(
                f"Event deleted: '{event_title}' (ID: {event_id_val}) "
                f"by User {current_user.id}"
            )

            return {"message": "Event deleted successfully", "event_id": event_id}, 200

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error in DELETE /events/{event_id}: {e}", exc_info=True)
            return error_response("Internal server error", 500)
