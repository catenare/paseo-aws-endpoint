import boto3
from flask import Flask, request, render_template, make_response, json
import requests
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

app.config.from_object(__name__)
app.config.update(dict(
  SECRET_KEY="THISISMYSECRETKEY",
  DB_TABLE="alpha_registration",
  CAPTCHA_KEY="6LcbXDQUAAAAAP2G436cLxoUhSdMJ_03lUDzhD2h",
  CAPTCHA_VERIFY_URL="https://www.google.com/recaptcha/api/siteverify"
))
app.config.from_envvar('FLASKR_SETTINGS', silent=True)

@app.route('/')
def home():
  return "hello world!"

@app.route('/register', methods=['POST'])
def register():
  registration = request.get_json()
  # print('Data Details:', request.values)
  response = make_response('0')
  verify = verify_captcha(registration)
  if verify == True:
    result = process_data(registration)
    response = make_response(result)
 
  return response

# Captcha verify
def verify_captcha(captcha):
  print("Captcha Details:", captcha)
  captcha_data = {
    'secret': app.config['CAPTCHA_KEY'],
    'response': captcha['captcha']
  }
  verify = requests.post(
    app.config['CAPTCHA_VERIFY_URL'], data=captcha_data
    )
  response = json.loads(verify.text)
  return response['success']

def process_data(data):
  result = '0';
  mail_template = render_template('mail.html', details=data)
  email_result = send_email(mail_template, data)
  db_result = add_entries(data)
  result = '1'
  return result

# dynamodb - database
def get_db():
  resource = boto3.resource('dynamodb')
  return resource

def get_table():
  resource = get_db()
  tables = resource.tables.all()
  for table in tables:
    if table.name == app.config['DB_TABLE']:
      return table
  table = create_table(resource)
  return table

def create_table(resource):
  table = resource.create_table(
    TableName=app.config['DB_TABLE'],
    KeySchema=[
      {
        'AttributeName':'uuid',
        'KeyType':'HASH'
      },
      {
        'AttributeName':'fullname',
        'KeyType':'RANGE'
      }
    ],
    AttributeDefinitions=[
      {
        'AttributeName':'uuid',
        'AttributeType':'S'
      },
      {
        'AttributeName':'fullname',
        'AttributeType':'S'
      }
    ],
    ProvisionedThroughput={
      'ReadCapacityUnits': 5,
      'WriteCapacityUnits': 5
    }
  )
  return table

def add_entries(data):
  table = get_table()
  response = table.put_item(
    Item={
      'uuid': data['uuid'],
      'fullname': data['fullname'],
      'mobile': data['mobile'],
      'postalcode': data['postalcode'],
      'age': data['age'],
      'email': data['email'],
      'time': data['time'],
      'fingerprint': data['fingerprint']
    }
  )
  return response


# Email
def get_ses():
  mail = boto3.client('ses', region_name='eu-west-1')
  return mail

def send_email(email_template, data):
  mail = get_ses()
  
  text_email = "Thank you for registering. Name:{}, Email: {}, Mobile: {}, Postal Code: {}, Age: {}".format(data['fullname'], data['email'], data['mobile'], data['postalcode'], data['age'])

  response = mail.send_email(
    Destination={
        'ToAddresses': [
            'alpha@paseo.org.za'
        ],
        'CcAddresses': [
            data['email']
        ]
    },
    Message={
        'Body': {
            'Html': {
                'Charset': 'UTF-8',
                'Data': email_template,
            },
            'Text': {
                'Charset': 'UTF-8',
                'Data': text_email,
            },
        },
        'Subject': {
            'Charset': 'UTF-8',
            'Data': 'Paseo Baptist Church Alpha Registration',
        },
    },
    ReplyToAddresses=[
      'info@paseo.org.za'
    ],
    ReturnPath='info@paseo.org.za',
    ReturnPathArn='arn:aws:ses:eu-west-1:338196870821:identity/paseo.org.za',
    Source='info@paseo.org.za',
    SourceArn='arn:aws:ses:eu-west-1:338196870821:identity/paseo.org.za'
  )
  return response

