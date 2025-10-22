from flask import request
from flask_restful import Resource
from tab_view.models import Device, Media, Event, db
from tab_view.utils import error_response
from .parser import event_parser, update_parser


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
        args = event_parser.parse_args()

        device = Device.query.get(args['device_id'])
        media = Media.query.get(args['media_id'])
        if not device:
            return error_response(f'Device with id {args["device_id"]} not found', 404)
        if not media:
            return error_response(f'Media with id {args["media_id"]} not found', 404)

        new_event = Event(
            title=args['title'],
            start_time=args['start_time'],
            end_time=args['end_time'],
            device_id=args['device_id'],
            media_id=args['media_id']
        )
        print(f'\n {args} \n')
        db.session.add(new_event)
        db.session.commit()
        return {'message': 'Event created',
                'event': new_event.to_dict()}, 201

    def put(self, event_id):
        event = Event.query.get_or_404(event_id)
        args = update_parser.parse_args()

        if args['device_id'] is not None:
            device = Device.query.get(args['device_id'])
            if not device:
                return error_response(f'Device with id {args["device_id"]} not found', 404)
            event.device_id = args['device_id']

        if args['media_id'] is not None:
            media = Media.query.get(args['media_id'])
            if not media:
                return error_response(f'Media with id {args["media_id"]} not found', 404)
            event.media_id = args['media_id']

        if args['title'] is not None:
            event.title = args['title']
        if args['start_time'] is not None:
            event.start_time = args['start_time']
        if args['end_time'] is not None:
            event.end_time = args['end_time']

        db.session.commit()
        return {'message': 'Event updated',
                'event': event.to_dict()}

    def delete(self, event_id):
        event = Event.query.get_or_404(event_id)
        db.session.delete(event)
        db.session.commit()
        return {'message': f'Event {event_id} deleted'}, 200
