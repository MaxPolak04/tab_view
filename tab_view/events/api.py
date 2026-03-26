import logging
import uuid
from datetime import datetime, timedelta

from flask import request
from flask_login import current_user, login_required
from flask_restful import Resource
from sqlalchemy import and_

from tab_view import limiter
from tab_view.models import Device, Event, EventMedia, db
from tab_view.utils import error_response

logger = logging.getLogger(__name__)


class EventAvailabilityResource(Resource):
    """
    Endpoint for live availability checking
    """

    @login_required
    def get(self):
        start_param = request.args.get("start")
        end_param = request.args.get("end")
        exclude_group = request.args.get("exclude_group_id")

        if not start_param or not end_param:
            return error_response("Missing start or end parameters", 400)

        try:
            start_time = datetime.fromisoformat(start_param.replace("Z", ""))
            end_time = datetime.fromisoformat(end_param.replace("Z", ""))
        except (ValueError, AttributeError):
            return error_response("Invalid date format", 400)

        query = Event.query.filter(
            Event.start_time < end_time,
            Event.end_time > start_time,
        )

        if exclude_group:
            query = query.filter(Event.group_id != exclude_group)

        overlapping_events = query.all()

        busy_devices = {}
        for ev in overlapping_events:
            busy_devices[ev.device_id] = {"busy": True, "event_title": ev.title}

        return busy_devices, 200


class EventResource(Resource):
    """
    REST API for event management
    """

    @login_required
    @limiter.limit("200 per hour")
    def get(self, event_id=None):
        try:
            if event_id:
                event = Event.query.get(event_id)
                if not event:
                    return error_response(f"Event with id {event_id} not found", 404)
                return event.to_dict(), 200

            device_id = request.args.get("device_id", type=int)
            start_param = request.args.get("start")
            end_param = request.args.get("end")

            if not start_param or not end_param:
                today = datetime.now()
                start_of_month = today.replace(
                    day=1, hour=0, minute=0, second=0, microsecond=0
                )
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
        try:
            data = request.get_json()
            if not data:
                return error_response("Request body must be JSON", 400)

            device_ids = data.get("device_ids", [])
            # Support fallback for legacy single-device calendar
            if "device_id" in data and not device_ids:
                device_ids = [data["device_id"]]

            if not device_ids:
                return error_response("Missing required field: device_ids", 400)

            required_fields = ["title", "start_time", "end_time", "media_playlist"]
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

            try:
                start_time = datetime.fromisoformat(data["start_time"].replace("Z", ""))
                end_time = datetime.fromisoformat(data["end_time"].replace("Z", ""))
            except (ValueError, AttributeError):
                return error_response("Invalid date format. Use ISO 8601 format.", 400)

            if start_time >= end_time:
                return error_response("End time must be after start time", 400)

            group_id = str(uuid.uuid4())
            created_events = []

            # Check overlap for all requested devices first
            for dev_id in device_ids:
                device = Device.query.get(dev_id)
                if not device:
                    return error_response(f"Device with id {dev_id} not found", 404)

                overlapping = Event.query.filter(
                    Event.device_id == dev_id,
                    Event.start_time < end_time,
                    Event.end_time > start_time,
                ).first()

                if overlapping:
                    return error_response(
                        f'Schedule overlap on device "{device.name}" \
                            with event "{overlapping.title}"',
                        409,
                    )

            # Create events for all selected devices
            for dev_id in device_ids:
                new_event = Event(
                    group_id=group_id,
                    title=data["title"].strip(),
                    start_time=start_time,
                    end_time=end_time,
                    device_id=dev_id,
                    color=data.get("color", "#3788d8"),
                )
                db.session.add(new_event)
                db.session.flush()

                for idx, item in enumerate(data["media_playlist"]):
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

                created_events.append(new_event)

            db.session.commit()
            return {
                "message": "Events created successfully",
                "events": [e.to_dict() for e in created_events],
            }, 201

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error in POST /events: {e}", exc_info=True)
            return error_response("Internal server error", 500)

    @login_required
    @limiter.limit("200 per hour")
    def put(self, event_id):
        try:
            event = Event.query.get(event_id)
            if not event:
                return error_response(f"Event with id {event_id} not found", 404)

            data = request.get_json()
            if not data:
                return error_response("Request body must be JSON", 400)

            group_id = event.group_id
            if not group_id:
                group_id = str(uuid.uuid4())

            device_ids = data.get("device_ids", [event.device_id])
            title = data.get("title", event.title).strip()
            color = data.get("color", event.color)

            try:
                start_time = datetime.fromisoformat(
                    data.get("start_time", event.start_time.isoformat()).replace(
                        "Z", ""
                    )
                )
                end_time = datetime.fromisoformat(
                    data.get("end_time", event.end_time.isoformat()).replace("Z", "")
                )
            except (ValueError, AttributeError):
                return error_response("Invalid date format", 400)

            if start_time >= end_time:
                return error_response("End time must be after start time", 400)

            for dev_id in device_ids:
                overlapping = Event.query.filter(
                    Event.device_id == dev_id,
                    Event.group_id != group_id,
                    Event.start_time < end_time,
                    Event.end_time > start_time,
                ).first()

                if overlapping:
                    dev = Device.query.get(dev_id)
                    logger.warning(
                        f"Event group update blocked - Overlap detected \
                            for Device {dev_id} ({dev.name}): "
                        f"'{overlapping.title}' (User: {current_user.id})"
                    )
                    return error_response(
                        f'Schedule overlap on device "{dev.name}" \
                            with event "{overlapping.title}"',
                        409,
                    )

            playlist_data = data.get("media_playlist")
            if playlist_data is None:
                playlist_data = [
                    {
                        "media_id": em.media_id,
                        "order": em.order,
                        "duration": em.duration,
                    }
                    for em in event.event_media
                ]

            if event.group_id:
                events_to_replace = Event.query.filter_by(group_id=event.group_id).all()
                for e in events_to_replace:
                    db.session.delete(e)
            else:
                db.session.delete(event)

            db.session.flush()

            updated_events = []
            for dev_id in device_ids:
                new_event = Event(
                    group_id=group_id,
                    title=title,
                    start_time=start_time,
                    end_time=end_time,
                    device_id=dev_id,
                    color=color,
                )
                db.session.add(new_event)
                db.session.flush()

                for idx, item in enumerate(playlist_data):
                    event_media = EventMedia(
                        event_id=new_event.id,
                        media_id=item["media_id"],
                        order=item.get("order", idx),
                        duration=item.get("duration", 10),
                    )
                    db.session.add(event_media)

                updated_events.append(new_event)

            db.session.commit()

            logger.info(
                f"Event group updated: '{title}' \
                    (Group ID: {group_id}, Devices: {device_ids}) "
                f"by User {current_user.id}"
            )

            return {
                "message": "Group events updated successfully",
                "events": [e.to_dict() for e in updated_events],
            }, 200

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error in PUT /events/{event_id}: {e}", exc_info=True)
            return error_response("Internal server error", 500)

    @login_required
    @limiter.limit("200 per hour")
    def delete(self, event_id):
        try:
            event = Event.query.get(event_id)
            if not event:
                return error_response(f"Event with id {event_id} not found", 404)

            group_id = event.group_id
            event_title = event.title

            if group_id:
                events_to_delete = Event.query.filter_by(group_id=group_id).all()
                for e in events_to_delete:
                    db.session.delete(e)
            else:
                db.session.delete(event)

            db.session.commit()

            logger.info(
                f"Event group deleted: '{event_title}' \
                    (Group ID: {group_id or 'None'})"
                f"by User {current_user.id}"
            )

            return {"message": "Event group deleted successfully"}, 200

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error in DELETE /events/{event_id}: {e}", exc_info=True)
            return error_response("Internal server error", 500)
