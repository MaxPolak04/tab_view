from flask_restful import reqparse
from datetime import datetime


event_parser = reqparse.RequestParser()
update_parser = reqparse.RequestParser()

event_parser.add_argument('title', type=str, required=True, help='Title is required')
# event_parser.add_argument('start_time', type=lambda x: datetime.strptime(x, '%Y-%m-%d %H:%M:%S'), required=True, help='start_time must be in format YYYY-MM-DD HH:MM:SS')
event_parser.add_argument('start_time', type=lambda x: datetime.fromisoformat(x.replace('Z', '+00:00')), required=True, help='start_time must be in format YYYY-MM-DD HH:MM:SS')
# event_parser.add_argument('end_time', type=lambda x: datetime.strptime(x, '%Y-%m-%d %H:%M:%S'), required=True, help='end_time must be in format YYYY-MM-DD HH:MM:SS')
event_parser.add_argument('end_time', type=lambda x: datetime.fromisoformat(x.replace('Z', '+00:00')), required=True, help='end_time must be in format YYYY-MM-DD HH:MM:SS')
event_parser.add_argument('device_id', type=int, required=True, help='device_id is missing')
event_parser.add_argument('media_id', type=int, required=True, help='media_id is missing')
# event_parser.add_argument('user_id', type=int, required=True, help='user_id is missing')


update_parser.add_argument('title', type=str)
update_parser.add_argument('start_time', type=lambda x: datetime.fromisoformat(x.replace('Z', '+00:00')))
update_parser.add_argument('end_time', type=lambda x: datetime.fromisoformat(x.replace('Z', '+00:00')))
update_parser.add_argument('device_id', type=int)
update_parser.add_argument('media_id', type=int)