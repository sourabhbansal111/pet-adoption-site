from flask import Flask, jsonify, request
from flask_restful import Resource, Api
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash # Keep if needed for other parts, otherwise remove
import os 

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "a_default_dev_secret_key")

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///contact_letter_v2.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

api = Api(app)

# --- Database Models ---

class ContactModel(db.Model):
    """SQLAlchemy model for storing contact request information."""
    __tablename__ = "contacts_table"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    number = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False) 
    location = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(20), nullable=False) 
    pname = db.Column(db.String(100), nullable=False)
    pid = db.Column(db.String(100), nullable=False)  
    status = db.Column(db.String(20), default='pending', nullable=False) 
    last_updated_by = db.Column(db.Integer, nullable=True) 

    def to_dict(self):

        return {
            "id": self.id,
            "username": self.username,
            "number": self.number,
            "email": self.email,
            "location": self.location,
            "message": self.message,
            "type": self.type,
            "pname": self.pname,
            "pid": self.pid,
            "status": self.status,
            "last_updated_by": self.last_updated_by 
        }

class LetterModel(db.Model):
    """SQLAlchemy model for storing newsletter/general contact letters."""
    __tablename__ = "letters_table"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    number = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='Not Viewed', nullable=False) 

    last_updated_by = db.Column(db.Integer, nullable=True) 

    def to_dict(self):
        """Converts the LetterModel object to a dictionary."""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "number": self.number,
            "location": self.location,
            "message": self.message,
            "status": self.status,
            "last_updated_by": self.last_updated_by 
        }

# --- API functions ---

class ContactResource(Resource):
    """API Resource for handling CRUD operations on Contacts."""

    def get(self, contact_id=None):
        """Handles GET requests to retrieve one or all contacts."""
        if contact_id:
            contact = ContactModel.query.get(contact_id)
            if not contact:
                return {"message": "Contact not found"}, 404
            return jsonify(contact.to_dict())
        else:
            contacts = ContactModel.query.all()
            return jsonify([c.to_dict() for c in contacts])

    def post(self):
        """Handles POST requests to add a new contact."""
        data = request.get_json()
        if not data:
            return {"message": "No input data provided"}, 400

        required_fields = ["username", "number", "email", "location", "message", "type", "pname", "pid"]
        if not all(field in data for field in required_fields):
            return {"message": f"Missing required fields: {', '.join(required_fields)}"}, 400

        if data['type'] not in ('adopt', 'service'):
             return {"message": "Invalid 'type'. Must be 'adopt' or 'service'."}, 400
        if 'status' in data and data['status'] not in ('accepted', 'declined', 'pending'):
             return {"message": "Invalid 'status'. Must be 'accepted', 'declined', or 'pending'."}, 400

        try:
            new_contact = ContactModel(
                username=data['username'],
                number=data['number'],
                email=data['email'],
                location=data['location'],
                message=data['message'],
                type=data['type'],
                pname=data['pname'],
                pid=data['pid'],
                status=data.get('status', 'pending'),
                last_updated_by=data.get('last_updated_by')
            )
            db.session.add(new_contact)
            db.session.commit()
            return {"message": "Contact created successfully", "contact": new_contact.to_dict()}, 201
        except Exception as e:
            db.session.rollback()
            return {"message": f"An error occurred: {str(e)}"}, 500

    def put(self, contact_id):
        """Handles PUT requests to update an existing contact (e.g., status)."""
        contact = ContactModel.query.get(contact_id)
        if not contact:
            return {"message": "Contact not found"}, 404

        data = request.get_json()
        if not data:
            return {"message": "No input data provided"}, 400
        updated = False
        if 'status' in data:
            if data['status'] not in ('accepted', 'declined', 'pending'):
                 return {"message": "Invalid 'status'. Must be 'accepted', 'declined', or 'pending'."}, 400
            contact.status = data['status']
            updated = True

        if 'last_updated_by' in data:
             contact.last_updated_by = data['last_updated_by'] 
             updated = True

        if 'username' in data:
            contact.username = data['username']
            updated = True

        if 'number' in data:
            contact.number = data['number']
            updated = True

        if 'email' in data:
            contact.email = data['email']
            updated = True

        if 'location' in data:
            contact.location = data['location']
            updated = True

        if 'message' in data:
            contact.message = data['message']
            updated = True

        if 'type' in data:
            if data['type'] not in ('adopt', 'service'):
                return {"message": "Invalid 'type'. Must be 'adopt' or 'service'."}, 400
            contact.type = data['type']
            updated = True

        if 'pname' in data:
            contact.pname = data['pname']
            updated = True

        if 'pid' in data:
            contact.pid = data['pid']
            updated = True


        if updated:
            try:
                db.session.commit()
                return {"message": "Contact updated successfully", "contact": contact.to_dict()}
            except Exception as e:
                db.session.rollback()
                return {"message": f"An error occurred during update: {str(e)}"}, 500
        else:
            return {"message": "No updateable fields provided"}, 400


    def delete(self, contact_id):
        """Handles DELETE requests to remove a contact."""
        contact = ContactModel.query.get(contact_id)
        if not contact:
            return {"message": "Contact not found"}, 404

        try:
            db.session.delete(contact)
            db.session.commit()
            return {"message": "Contact deleted successfully"}, 200
        except Exception as e:
            db.session.rollback()
            return {"message": f"An error occurred during deletion: {str(e)}"}, 500


class LetterResource(Resource):
    """API Resource for handling CRUD operations on Letters."""

    def get(self, letter_id=None):
        """Handles GET requests to retrieve one or all letters."""
        if letter_id:
            letter = LetterModel.query.get(letter_id)
            if not letter:
                return {"message": "Letter not found"}, 404
            return jsonify(letter.to_dict())
        else:
            letters = LetterModel.query.all()
            return jsonify([l.to_dict() for l in letters])

    def post(self):
        """Handles POST requests to add a new letter."""
        data = request.get_json()
        if not data:
            return {"message": "No input data provided"}, 400

        required_fields = ["username", "email", "number", "location", "message"]
        if not all(field in data for field in required_fields):
            return {"message": f"Missing required fields: {', '.join(required_fields)}"}, 400

        if 'status' in data and data['status'] not in ('Not Viewed', 'Viewed'):
             return {"message": "Invalid 'status'. Must be 'Not Viewed' or 'Viewed'."}, 400

        try:
            new_letter = LetterModel(
                username=data['username'],
                email=data['email'],
                number=data['number'],
                location=data['location'],
                message=data['message'],
                status=data.get('status', 'Not Viewed'),
                 # Expect 'last_updated_by' in payload now
                last_updated_by=data.get('last_updated_by')
            )
            db.session.add(new_letter)
            db.session.commit()
            return {"message": "Letter created successfully", "letter": new_letter.to_dict()}, 201
        except Exception as e:
            db.session.rollback()
            return {"message": f"An error occurred: {str(e)}"}, 500

    def put(self, letter_id):
        """Handles PUT requests to update an existing letter (e.g., status)."""
        letter = LetterModel.query.get(letter_id)
        if not letter:
            return {"message": "Letter not found"}, 404
        data = request.get_json()
        if not data:
            return {"message": "No input data provided"}, 400

        updated = False
        if 'status' in data:
            if data['status'] not in ('Not Viewed', 'Viewed'):
                 return {"message": "Invalid 'status'. Must be 'Not Viewed' or 'Viewed'."}, 400
            letter.status = data['status']
            updated = True

        if 'last_updated_by' in data:
            letter.last_updated_by = data['last_updated_by']
            updated = True

        if 'username' in data:
            letter.username = data['username']
            updated = True

        if 'email' in data:
            letter.email = data['email']
            updated = True

        if 'number' in data:
            letter.number = data['number']
            updated = True

        if 'location' in data:
            letter.location = data['location']
            updated = True

        if 'message' in data:
            letter.message = data['message']
            updated = True


        if updated:
            try:
                db.session.commit()
                return {"message": "Letter updated successfully", "letter": letter.to_dict()}
            except Exception as e:
                db.session.rollback()
                return {"message": f"An error occurred during update: {str(e)}"}, 500
        else:
             return {"message": "No updateable fields provided"}, 400


    def delete(self, letter_id):
        """Handles DELETE requests to remove a letter."""
        letter = LetterModel.query.get(letter_id)
        if not letter:
            return {"message": "Letter not found"}, 404

        try:
            db.session.delete(letter)
            db.session.commit()
            return {"message": "Letter deleted successfully"}, 200
        except Exception as e:
            db.session.rollback()
            return {"message": f"An error occurred during deletion: {str(e)}"}, 500


# --- API Endpoint Routing ---
api.add_resource(ContactResource,
                 "/contacts",  # For GET (all), POST
                 "/contacts/<int:contact_id>") # For GET (one), PUT, DELETE

api.add_resource(LetterResource,
                 "/letters",   # For GET (all), POST
                 "/letters/<int:letter_id>")  # For GET (one), PUT, DELETE


with app.app_context():
    db.create_all()
    print("Database tables created .")


# --- Run Flask App ---
if __name__ == "__main__":
    app.run(debug=True, port=5001)
