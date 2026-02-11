from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail

db=SQLAlchemy()
mail=Mail()
cors = CORS()