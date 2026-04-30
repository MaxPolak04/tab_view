import logging
import uuid
from datetime import datetime, timedelta

from flask import request
from flask_login import current_user, login_required
from flask_restful import Resource
from sqlalchemy import and_

from tab_view import limiter
from tab_view.models import Device, Event, EventMedia, db
from tab_view.utils import error_response, log_audit_action

logger = logging.getLogger(__name__)


class EventAvailabilityResource(Resource):
    """
    Endpoint for live availability checking
    """

    @login_required
    def get(self):
        """
        Check device availability for a specific time range.
        """
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
        """
        Retrieve events or a specific event by ID.
        """
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
        """
        Create a new event or group of events across multiple devices.
        """
        try:
            data = request.get_json()
            if not data:
                return error_response("Request body must be JSON", 400)

            device_ids = data.get("device_ids", [])
            if "device_id" in data and not device_ids:
                device_ids = [data["device_id"]]

            if not device_ids:
                return error_response("Missing required field: device_ids", 400)

            required_fields = ["title", "start_time", "end_time"]
            missing_fields = [field for field in required_fields if not data.get(field)]

            if missing_fields:
                return error_response(
                    f"Missing required fields: {', '.join(missing_fields)}", 400
                )

            if not isinstance(data["title"], str) or len(data["title"].strip()) == 0:
                return error_response("Title must be a non-empty string", 400)

            if len(data["title"]) > 50:
                return error_response("Title is too long (max 50 characters)", 400)

            if not isinstance(data.get("media_playlist", []), list):
                return error_response("Playlist must be an array", 400)

            try:
                start_time = datetime.fromisoformat(data["start_time"].replace("Z", ""))
                end_time = datetime.fromisoformat(data["end_time"].replace("Z", ""))
            except (ValueError, AttributeError):
                return error_response("Invalid date format. Use ISO 8601 format.", 400)

            if start_time >= end_time:
                return error_response("End time must be after start time", 400)

            show_clock = data.get("show_clock", False)

            group_id = str(uuid.uuid4())
            created_events = []

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

            for dev_id in device_ids:
                new_event = Event(
                    group_id=group_id,
                    title=data["title"].strip(),
                    start_time=start_time,
                    end_time=end_time,
                    device_id=dev_id,
                    color=data.get("color", "#3788d8"),
                    show_clock=show_clock,
                )
                db.session.add(new_event)
                db.session.flush()

                for idx, item in enumerate(data.get("media_playlist", [])):
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

            log_audit_action(
                "CREATE",
                "Event",
                f"Created event '{data['title'].strip()}' \
                    on {len(device_ids)} device(s).",
            )

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
        """
        Update an existing event or event group.
        Accepts '?scope=instance' or '?scope=group' to determine behavior.
        """
        try:
            event = Event.query.get(event_id)
            if not event:
                return error_response(f"Event with id {event_id} not found", 404)

            data = request.get_json()
            if not data:
                return error_response("Request body must be JSON", 400)

            scope = request.args.get("scope", "group")

            title = data.get("title", event.title).strip()
            color = data.get("color", event.color)
            show_clock = data.get("show_clock", event.show_clock)

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

            # Determine scope of operation
            if scope == "instance":
                group_id = str(uuid.uuid4())  # Detach from existing group
                device_ids = [event.device_id]
                events_to_delete = [event]
            else:
                group_id = event.group_id or str(uuid.uuid4())
                device_ids = data.get("device_ids", [event.device_id])
                if event.group_id:
                    events_to_delete = Event.query.filter_by(
                        group_id=event.group_id
                    ).all()
                else:
                    events_to_delete = [event]

            ignore_ids = [e.id for e in events_to_delete]

            for dev_id in device_ids:
                overlapping = Event.query.filter(
                    Event.device_id == dev_id,
                    Event.id.notin_(ignore_ids),
                    Event.start_time < end_time,
                    Event.end_time > start_time,
                ).first()

                if overlapping:
                    dev = Device.query.get(dev_id)
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

            for e in events_to_delete:
                db.session.delete(e)

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
                    show_clock=show_clock,
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

            op_type = "instance" if scope == "instance" else "group"
            log_audit_action("UPDATE", "Event", f"Updated event {op_type} '{title}'.")

            return {
                "message": f"Event {op_type} updated successfully",
                "events": [e.to_dict() for e in updated_events],
            }, 200

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error in PUT /events/{event_id}: {e}", exc_info=True)
            return error_response("Internal server error", 500)

    @login_required
    @limiter.limit("200 per hour")
    def delete(self, event_id):
        """
        Delete an event instance or its entire associated group.
        Accepts '?scope=instance' or '?scope=group'
        """
        try:
            event = Event.query.get(event_id)
            if not event:
                return error_response(
                    f"Event with id \
                                      {event_id} not found",
                    404,
                )

            scope = request.args.get("scope", "group")
            group_id = event.group_id
            event_title = event.title

            if scope == "instance":
                db.session.delete(event)
                log_msg = f"Deleted instance of event \
                    '{event_title}' on device {event.device_id}."
            else:
                if group_id:
                    events_to_delete = Event.query.filter_by(group_id=group_id).all()
                    for e in events_to_delete:
                        db.session.delete(e)
                else:
                    db.session.delete(event)
                log_msg = f"Deleted event group '{event_title}'."

            db.session.commit()

            logger.info(f"Admin {current_user.id} {log_msg.lower()}")
            log_audit_action("DELETE", "Event", log_msg)

            return {"message": "Operation successful"}, 200

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error in DELETE /events/{event_id}: {e}", exc_info=True)
            return error_response("Internal server error", 500)
