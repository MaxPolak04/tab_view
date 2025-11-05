from flask import request
from flask_restful import Resource
from tab_view.models import Device, Media, Event, EventMedia, db
from tab_view.utils import error_response
from datetime import datetime


class EventResource(Resource):
    def get(self):
        device_id = request.args.get('device_id', type=int)

        if device_id:
            events = Event.query.filter_by(device_id=device_id).all()
        else:
            events = Event.query.all()

        result = [event.to_dict() for event in events]
        return result, 200
    

    def post(self):
        data = request.get_json()
        
        if not data.get('title') or not data.get('start_time') or not data.get('end_time'):
            return error_response('Missing required fields', 400)
        
        if not data.get('media_playlist') or len(data['media_playlist']) == 0:
            return error_response('Playlist cannot be empty', 400)
        
        device = Device.query.get(data['device_id'])
        if not device:
            return error_response(f'Device with id {data["device_id"]} not found', 404)
        
        new_event = Event(
            title=data['title'],
            start_time=datetime.fromisoformat(data['start_time']),
            end_time=datetime.fromisoformat(data['end_time']),
            device_id=data['device_id'],
            color=data.get('color', data['color'])
        )
        db.session.add(new_event)
        db.session.flush()

        for item in data['media_playlist']:
            media = Media.query.get(item['media_id'])
            if not media:
                db.session.rollback()
                return error_response(f'Media with id {item["media_id"]} not found', 404)
            
            event_media = EventMedia(
                event_id=new_event.id,
                media_id=item['media_id'],
                order=item.get('order', 0),
                duration=item.get('duration', 10)
            )
            db.session.add(event_media)
        
        db.session.commit()
        return {'message': 'Event created', 'event': new_event.to_dict()}, 201


    def put(self, event_id):
        event = Event.query.get_or_404(event_id)
        data = request.get_json()

        if data.get('title'):
            event.title = data['title']
        if data.get('start_time'):
            event.start_time = datetime.fromisoformat(data['start_time'])
        if data.get('end_time'):
            event.end_time = datetime.fromisoformat(data['end_time'])  
        if data.get('color'):
            event.color = data['color']

        if 'media_playlist' in data:
            EventMedia.query.filter_by(event_id=event.id).delete()

            for item in data['media_playlist']:
                media = Media.query.get(item['media_id'])
                if not media:
                    db.session.rollback()
                    return error_response(f'Media with id {item["media_id"]} not found', 404)
                
                event_media = EventMedia(
                    event_id=event.id,
                    media_id=item['media_id'],
                    order=item.get('order', 0),
                    duration=item.get('duration', 10)
                )
                db.session.add(event_media)
        
        db.session.commit()
        return {'message': 'Event updated', 'event': event.to_dict()}


    def delete(self, event_id):
        event = Event.query.get_or_404(event_id)
        db.session.delete(event)
        db.session.commit()
        return {'message': f'Event {event_id} deleted'}, 200
