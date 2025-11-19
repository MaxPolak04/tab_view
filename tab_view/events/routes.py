from flask import request, jsonify
from flask_restful import Resource
from flask_login import login_required
from sqlalchemy import and_
from tab_view import limiter
from tab_view.models import Device, Media, Event, EventMedia, db
from tab_view.utils import error_response
from datetime import datetime, timedelta
import logging


logger = logging.getLogger(__name__)


class EventResource(Resource):
    """
    REST API for event management
    """
    @login_required
    @limiter.limit('200 per hour')
    def get(self, event_id=None):
        """
        GET /api/v1/events/ - List of events (filtered by device and date)
        GET /api/v1/events/<id> - Single event
        
        Query params:
        - device_id: int - filter by device
        - start: ISO date - start of range (default: first day of the current month)
        - end: ISO date - end of range (default: last day of the current month)
        """
        try:
            # Single event
            if event_id:
                event = Event.query.get(event_id)
                if not event:
                    return error_response(f'Event with id {event_id} not found', 404)
                return event.to_dict(), 200
            
            # List of events with filtering
            device_id = request.args.get('device_id', type=int)
            start_param = request.args.get('start')
            end_param = request.args.get('end')
            
            # Default range: current month
            if not start_param or not end_param:
                today = datetime.now()
                start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                
                # The last day of the month
                if today.month == 12:
                    end_of_month = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
                else:
                    end_of_month = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
                end_of_month = end_of_month.replace(hour=23, minute=59, second=59)
            else:
                # Parse parameters from FullCalendar
                try:
                    start_of_month = datetime.fromisoformat(start_param.replace('Z', ''))
                    end_of_month = datetime.fromisoformat(end_param.replace('Z', ''))
                except (ValueError, AttributeError) as e:
                    logger.error(f"Date parsing error: {e}")
                    return error_response('Invalid date format. Use ISO 8601 format.', 400)
            
            # Build a query
            query = Event.query
            
            # Filter by device
            if device_id:
                if not Device.query.get(device_id):
                    return error_response(f'Device with id {device_id} not found', 404)
                query = query.filter(Event.device_id == device_id)
            
            # Filter by date range (events that fall within the selected range)
            query = query.filter(
                and_(
                    Event.start_time <= end_of_month,
                    Event.end_time >= start_of_month
                )
            )
            
            # Sort by start date
            query = query.order_by(Event.start_time.asc())
            
            events = query.all()
            result = [event.to_dict() for event in events]
            
            logger.info(f"{len(result)} events downloaded for device_id={device_id}, range: {start_of_month} - {end_of_month}")
            return result, 200
            
        except Exception as e:
            logger.error(f"Error in GET /events: {e}", exc_info=True)
            return error_response('Internal server error', 500)
    

    @login_required
    @limiter.limit('200 per hour')
    def post(self):
        """
        POST /api/v1/events/ - Create new event
        
        Body JSON:
        {
            "title": str,
            "start_time": ISO datetime,
            "end_time": ISO datetime,
            "device_id": int,
            "color": str (hex color),
            "media_playlist": [
                {
                    "media_id": int,
                    "order": int,
                    "duration": int
                }
            ]
        }
        """
        
        try:
            data = request.get_json()
            
            if not data:
                return error_response('Request body must be JSON', 400)
            
            # Validation of required fields
            required_fields = ['title', 'start_time', 'end_time', 'device_id', 'media_playlist']
            missing_fields = [field for field in required_fields if not data.get(field)]
            
            if missing_fields:
                return error_response(f'Missing required fields: {", ".join(missing_fields)}', 400)
            
            # Validation title
            if not isinstance(data['title'], str) or len(data['title'].strip()) == 0:
                return error_response('Title must be a non-empty string', 400)
            
            if len(data['title']) > 50:
                return error_response('Title is too long (max 50 characters)', 400)
            
            # Playlist validation
            if not isinstance(data['media_playlist'], list) or len(data['media_playlist']) == 0:
                return error_response('Playlist must be a non-empty array', 400)
            
            # Device validation
            device = Device.query.get(data['device_id'])
            if not device:
                return error_response(f'Device with id {data["device_id"]} not found', 404)
            
            # Date parsing
            try:
                start_time = datetime.fromisoformat(data['start_time'].replace('Z', ''))
                end_time = datetime.fromisoformat(data['end_time'].replace('Z', ''))
            except (ValueError, AttributeError) as e:
                logger.error(f"Date parsing error: {e}")
                return error_response('Invalid date format. Use ISO 8601 format.', 400)
            
            # Date logic validation
            if start_time >= end_time:
                return error_response('End time must be after start time', 400)
            
            # Check overlapping events
            overlapping = Event.query.filter(
                Event.device_id == data['device_id'],
                Event.start_time < end_time,
                Event.end_time > start_time
            ).first()
            
            if overlapping:
                logger.warning(f"Overlapping event: {overlapping.id}")
                # return error_response('Event overlaps with existing event', 409)
            
            # create event
            new_event = Event(
                title=data['title'].strip(),
                start_time=start_time,
                end_time=end_time,
                device_id=data['device_id'],
                color=data.get('color', data['color'])
            )
            db.session.add(new_event)
            db.session.flush()  # Get the ID without committing
            
            # Add media to playlist
            for idx, item in enumerate(data['media_playlist']):
                if not isinstance(item, dict):
                    db.session.rollback()
                    return error_response(f'Playlist item {idx} must be an object', 400)
                
                if 'media_id' not in item:
                    db.session.rollback()
                    return error_response(f'Playlist item {idx} missing media_id', 400)
                
                media = Media.query.get(item['media_id'])
                if not media:
                    db.session.rollback()
                    return error_response(f'Media with id {item["media_id"]} not found', 404)
                
                # Duration validation
                duration = item.get('duration', 10)
                if not isinstance(duration, int) or duration < 1 or duration > 300:
                    duration = 10
                
                event_media = EventMedia(
                    event_id=new_event.id,
                    media_id=item['media_id'],
                    order=item.get('order', idx),
                    duration=duration
                )
                db.session.add(event_media)
            
            db.session.commit()
            logger.info(f"Event {new_event.id} has been created: {new_event.title}")
            
            return {
                'message': 'Event created successfully',
                'event': new_event.to_dict()
            }, 201
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error in POST /events: {e}", exc_info=True)
            return error_response('Internal server error', 500)


    @login_required
    @limiter.limit('200 per hour')
    def put(self, event_id):
        """
        PUT /api/v1/events/<id> - Update event
        
        Body JSON: (all optional fields)
        {
            "title": str,
            "start_time": ISO datetime,
            "end_time": ISO datetime,
            "color": str,
            "media_playlist": [...]
        }
        """
        try:
            event = Event.query.get(event_id)
            if not event:
                return error_response(f'Event with id {event_id} not found', 404)
            
            data = request.get_json()
            if not data:
                return error_response('Request body must be JSON', 400)
            
            # Update title
            if 'title' in data:
                if not isinstance(data['title'], str) or len(data['title'].strip()) == 0:
                    return error_response('Title must be a non-empty string', 400)
                if len(data['title']) > 50:
                    return error_response('Title is too long (max 50 characters)', 400)
                event.title = data['title'].strip()
            
            # Update date
            if 'start_time' in data:
                try:
                    event.start_time = datetime.fromisoformat(data['start_time'].replace('Z', ''))
                except (ValueError, AttributeError):
                    return error_response('Invalid start_time format', 400)
            
            if 'end_time' in data:
                try:
                    event.end_time = datetime.fromisoformat(data['end_time'].replace('Z', ''))
                except (ValueError, AttributeError):
                    return error_response('Invalid end_time format', 400)
            
            # Date logic validation
            if event.start_time >= event.end_time:
                return error_response('End time must be after start time', 400)
            
            # Update color
            if 'color' in data:
                color = data['color']
                if isinstance(color, str) and color.startswith('#') and len(color) == 7:
                    event.color = color
            
            # Update playlist
            if 'media_playlist' in data:
                if not isinstance(data['media_playlist'], list):
                    return error_response('Playlist must be an array', 400)
                
                if len(data['media_playlist']) == 0:
                    return error_response('Playlist cannot be empty', 400)
                
                # Delete old playlist
                EventMedia.query.filter_by(event_id=event.id).delete()
                
                # Add new playlist
                for idx, item in enumerate(data['media_playlist']):
                    if not isinstance(item, dict):
                        db.session.rollback()
                        return error_response(f'Playlist item {idx} must be an object', 400)
                    
                    if 'media_id' not in item:
                        db.session.rollback()
                        return error_response(f'Playlist item {idx} missing media_id', 400)
                    
                    media = Media.query.get(item['media_id'])
                    if not media:
                        db.session.rollback()
                        return error_response(f'Media with id {item["media_id"]} not found', 404)
                    
                    duration = item.get('duration', 10)
                    if not isinstance(duration, int) or duration < 1 or duration > 300:
                        duration = 10
                    
                    event_media = EventMedia(
                        event_id=event.id,
                        media_id=item['media_id'],
                        order=item.get('order', idx),
                        duration=duration
                    )
                    db.session.add(event_media)
            
            db.session.commit()
            logger.info(f"Event {event.id} has been updated.")
            
            return {
                'message': 'Event updated successfully',
                'event': event.to_dict()
            }, 200
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error in PUT /events/{event_id}: {e}", exc_info=True)
            return error_response('Internal server error', 500)


    @login_required
    @limiter.limit('200 per hour')
    def delete(self, event_id):
        """
        DELETE /api/v1/events/<id> - Deletw event
        """
        try:
            event = Event.query.get(event_id)
            if not event:
                return error_response(f'Event with id {event_id} not found', 404)
            
            event_title = event.title
            db.session.delete(event)  # EventMedia will be removed by cascade
            db.session.commit()
            
            logger.info(f"Event {event_id} has been deleted.: {event_title}")
            
            return {
                'message': f'Event deleted successfully',
                'event_id': event_id
            }, 200
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error in DELETE /events/{event_id}: {e}", exc_info=True)
            return error_response('Internal server error', 500)
