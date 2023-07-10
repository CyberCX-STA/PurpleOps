import datetime
from flask import jsonify
from flask_mongoengine import MongoEngine
from bson.objectid import ObjectId
from flask_security import UserMixin, RoleMixin, MongoEngineUserDatastore

db = MongoEngine()

class Tactic(db.Document):
    mitreid = db.StringField()
    name = db.StringField()


class Technique(db.Document):
    mitreid = db.StringField()
    name = db.StringField()
    description = db.StringField()
    detection = db.StringField()
    tactics = db.ListField(db.StringField())


# TODO how to generalise? 4x same object
class Source(db.EmbeddedDocument):
    id = db.ObjectIdField( required=True, default=ObjectId )
    name = db.StringField()
    description = db.StringField()

    def to_json(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description
        }


class Target(db.EmbeddedDocument):
    id = db.ObjectIdField( required=True, default=ObjectId )
    name = db.StringField()
    description = db.StringField()

    def to_json(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description
        }


class Tool(db.EmbeddedDocument):
    id = db.ObjectIdField( required=True, default=ObjectId )
    name = db.StringField()
    description = db.StringField()

    def to_json(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description
        }


class Control(db.EmbeddedDocument):
    id = db.ObjectIdField( required=True, default=ObjectId )
    name = db.StringField()
    description = db.StringField()

    def to_json(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description
        }


class Tag(db.EmbeddedDocument):
    id = db.ObjectIdField( required=True, default=ObjectId )
    name = db.StringField()
    colour = db.StringField()

    def to_json(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "colour": self.colour # AU spelling is non-negotiable xx
        }


class File(db.EmbeddedDocument):
    name = db.StringField()
    path = db.StringField()
    caption = db.StringField(default="")


class KnowlegeBase(db.Document):
    mitreid = db.StringField()
    overview = db.StringField()
    advice = db.StringField()
    provider = db.StringField()


class Sigma(db.Document):
    mitreid = db.StringField()
    name = db.StringField()
    description = db.StringField()
    url = db.StringField()


class TestCaseTemplate(db.Document):
    name = db.StringField()
    mitreid = db.StringField(default="")
    tactic = db.StringField(default="")
    objective = db.StringField(default="")
    actions = db.StringField(default="")
    rednotes = db.StringField(default="")
    provider = db.StringField(default="")


class TestCase(db.Document):
    assessmentid = db.StringField()
    name = db.StringField()
    objective = db.StringField(default="")
    actions = db.StringField(default="")
    rednotes = db.StringField(default="")
    bluenotes = db.StringField(default="")
    mitreid = db.StringField()
    tactic = db.StringField()
    sources = db.ListField(db.StringField())
    targets = db.ListField(db.StringField())
    tools = db.ListField(db.StringField())
    controls = db.ListField(db.StringField())
    tags = db.ListField(db.StringField())
    state = db.StringField(default="Pending")
    prevented = db.StringField()
    preventedrating = db.StringField()
    alerted = db.BooleanField()
    alertseverity = db.StringField()
    logged = db.BooleanField()
    detectionrating = db.StringField()
    priority = db.StringField()
    priorityurgency = db.StringField()
    starttime = db.DateTimeField()
    endtime = db.DateTimeField()
    detecttime = db.DateTimeField()
    redfiles = db.EmbeddedDocumentListField(File)
    bluefiles = db.EmbeddedDocumentListField(File)
    visible = db.BooleanField(default=False)
    modifytime = db.DateTimeField()

    def to_json(self):
        jsonDict = {}
        assessment = Assessment.objects(id=self.assessmentid).first()
        for field in ["assessmentid", "name", "objective", "actions", "rednotes", "bluenotes",
                      "mitreid", "tactic", "state", "prevented", "preventedrating",
                      "alerted", "alertseverity", "logged", "detectionrating",
                      "priority", "priorityurgency", "starttime", "endtime",
                      "detecttime", "visible", "modifytime"]:
            jsonDict[field] = self[field]
        for field in ["id", "detecttime", "modifytime", "starttime", "endtime"]:
            jsonDict[field] = str(self[field])
        for field in ["tags", "sources", "targets", "tools", "controls"]:
            strs = []
            for i in self[field]:
                strs.append([j.name for j in assessment[field] if str(j.id) == i][0])
            jsonDict[field] = strs
        for field in ["redfiles", "bluefiles"]:
            files = []
            for file in self[field]:
                files.append(f"{file.path}|{file.caption}")
            jsonDict[field] = files
        return jsonDict


class Assessment(db.Document):
    name = db.StringField()
    description = db.StringField()
    created = db.DateTimeField(default=datetime.datetime.utcnow)
    targets = db.EmbeddedDocumentListField(Target)
    sources = db.EmbeddedDocumentListField(Source)
    tools = db.EmbeddedDocumentListField(Tool)
    controls = db.EmbeddedDocumentListField(Control)
    tags = db.EmbeddedDocumentListField(Tag)

    # def get_status(self):
    #     pending = TestCase.objects(assessmentid=str(self.id),state="Pending").count()
    #     completed = TestCase.objects(assessmentid=str(self.id),state="Complete").count()
    #     total = TestCase.objects(assessmentid=str(self.id)).count()
        
    #     if total > 0:
    #         pending_percent = int((completed / total) * 100)
    #     else:
    #         pending_percent = 0
    #     completed_percent = 100 - pending_percent
    #     return {"pending": pending,
    #         "completed": completed,
    #         "total": total,
    #         "pending_percent": pending_percent,
    #         "completed_percent": completed_percent}
        

    def to_json(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "progress": 75
        }
                    
    def multi_to_json(self, field):
        return [item.to_json() for item in self[field]]


class Role(db.Document, RoleMixin):
    name = db.StringField(max_length=80, unique=True)
    description = db.StringField(max_length=255, default="")


class User(db.Document, UserMixin):
    email = db.StringField(max_length=255)
    username = db.StringField(max_length=255, unique=True, nullable=True)
    password = db.StringField(max_length=255)
    roles = db.ListField(db.ReferenceField(Role), default=[])
    assessments = db.ListField(db.ReferenceField(Assessment), default=[])
    initpwd = db.BooleanField(default=True)
    active = db.BooleanField(default=True)

    last_login_at = db.DateTimeField()
    current_login_at = db.DateTimeField()
    last_login_ip = db.StringField()
    current_login_ip = db.StringField()
    login_count = db.IntField()

    fs_uniquifier = db.StringField(max_length=255, unique=True)
    tf_primary_method = db.StringField(max_length=64, nullable=True)
    tf_totp_secret = db.StringField(max_length=255, nullable=True)

    def assessment_list(self):
        if "Admin" in [r.name for r in self.roles]:
            return [a.id for a in Assessment.objects()]
        else:
            return [a.id for a in self.assessments]
        
    def to_json(self):
        return {
            "id": str(self.id),
            "username": self.username,
            "email": self.email,
            "roles": [r.name for r in self.roles],
            "assessments": [a.name for a in self.assessments],
            "last_login_at": self.last_login_at,
            "current_login_ip": self.current_login_ip,
            "last_login_ip": self.last_login_ip
        }


user_datastore = MongoEngineUserDatastore(db, User, Role)