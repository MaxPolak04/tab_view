from flask_restful import Resource
from tab_view.models import Event, db
from .parser import event_parser, update_parser


class EventResource(Resource):
    def get(self):
        events = Event.query.all()
        result = []
        for event in events:
            result.append({
                'id': event.id,
                'title': event.title,
                'start_time': event.start_time.strftime('%Y-%m-%dT%H:%M:%S'),
                'end_time': event.end_time.strftime('%Y-%m-%dT%H:%M:%S'),
                'device_id': event.device_id,
                'media_id': event.media_id,
            })
        return result, 200
    
    def post(self):
        args = event_parser.parse_args()
        new_event = Event(
            title=args['title'],
            start_time=args['start_time'],
            end_time=args['end_time'],
            device_id=args['device_id'],
            media_id=args['media_id']
        )
        db.session.add(new_event)
        db.session.commit()
        return {'message': 'Event created',
                'event': new_event.to_dict()}, 201

    def put(self, event_id):
        event = Event.query.get_or_404(event_id)
        args = update_parser.parse_args()

        event.title = args['title']
        event.start_time = args['start_time']
        event.end_time = args['end_time']
        event.device_id = args['device_id']
        event.media_id = args['media_id']

        db.session.commit()
        return {'message': 'Event updated',
                'event': event.to_dict()}

    def delete(self, event_id):
        event = Event.query.get_or_404(event_id)
        db.session.delete(event)
        db.session.commit()
        return {'message': f'Event {event_id} deleted'}, 200
