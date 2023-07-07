import datetime
from flask import jsonify
from flask_mongoengine import MongoEngine
from bson.objectid import ObjectId
from flask_security import UserMixin, RoleMixin, MongoEngineUserDatastore

db = MongoEngine()

class Tactic(db.Document):
    mitreid = db.StringField()
    name = db.StringField()
    # url = db.StringField()
    # description = db.StringField()
    # created = db.StringField()
    # lastmodified = db.StringField()

    def to_json(self):
        return None


class Technique(db.Document):
    mitreid = db.StringField()
    name = db.StringField()
    description = db.StringField()
    detection = db.StringField()
    tactics = db.ListField(db.StringField())
    # url = db.StringField()
    # datasources = db.ListField(db.StringField())
    # created = db.StringField()
    # lastmodified = db.StringField()
    # version = db.StringField()
    # platforms = db.ListField(db.StringField())
    # issubtechnique = db.StringField()
    # subtechniqueof = db.StringField()
    # contributors = db.StringField()
    # systemrequirements = db.ListField(db.StringField())
    # permissionsrequired = db.ListField(db.StringField())
    # effectivepermissions = db.StringField()
    # defensesbypassed = db.ListField(db.StringField())
    # impacttype = db.StringField()
    # supportsremote = db.StringField()

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
            "colour": self.colour
        }


# class Reference(db.EmbeddedDocument):
#     name = db.StringField()
#     url = db.StringField()


class File(db.EmbeddedDocument):
    name = db.StringField()
    path = db.StringField()
    caption = db.StringField(default="")


class KnowlegeBase(db.Document):
    mitreid = db.StringField()
    overview = db.StringField()
    advice = db.StringField()
    provider = db.StringField()
#     references = db.EmbeddedDocumentListField(Reference)

class Sigma(db.Document):
    mitreid = db.StringField()
    name = db.StringField()
    description = db.StringField()
    url = db.StringField()
    # filename = db.StringField()
    # raw = db.StringField()

class TestCaseTemplate(db.Document):
    name = db.StringField()
    mitreid = db.StringField(default="")
    tactic = db.StringField(default="")
    objective = db.StringField(default="")
    actions = db.StringField(default="")
    rednotes = db.StringField(default="")
    provider = db.StringField(default="")
    # advice = db.StringField(default="")
    # overview = db.StringField()
    # html = db.StringField(default="")
    # mitretitle = db.StringField(default="")
    # state = db.StringField(default="")
    # location = db.StringField(default="")
    # kbentry = db.BooleanField(default=False)
    # references = db.EmbeddedDocumentListField(Reference)

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
    blocked = db.StringField()
    blockedrating = db.StringField()
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
    # overview = db.StringField()
    # advice = db.StringField()
    # references = db.EmbeddedDocumentListField(Reference)
    # location = db.StringField()
    # provider = db.StringField()
    # kbentry = db.BooleanField(default=False)

    def to_json(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "mitreid": self.mitreid,
            "tactic": self.tactic,
            "state": self.state,
            "tags": [], #self.assessment_refs_to_str("tags"),
            "visible": str(self.visible).lower()
        }
    
    def assessment_refs_to_str(self, field):
        assessment = Assessment.objects(id=self.assessmentid).first()
        strs = []
        for i in self[field]:
            strs.append([j.name for j in assessment[field] if str(j.id) == i][0])
        return strs

    def starttime_tostring(self):
        if not self.starttime:
            return ""
        else:
            return self.starttime.strftime("%d/%m/%Y, %I:%M %p")

    def endtime_tostring(self):
        if not self.endtime:
            return ""
        else:
            return self.endtime.strftime("%d/%m/%Y, %I:%M %p")


class Assessment(db.Document):
    name = db.StringField()
    description = db.StringField()
    created = db.DateTimeField(default=datetime.datetime.utcnow)
    targets = db.EmbeddedDocumentListField(Target)
    sources = db.EmbeddedDocumentListField(Source)
    tools = db.EmbeddedDocumentListField(Tool)
    controls = db.EmbeddedDocumentListField(Control)
    tags = db.EmbeddedDocumentListField(Tag)
    # industry = db.StringField()
    # techmaturity = db.StringField()
    # opmaturity = db.StringField()
    # socmodel = db.StringField()
    # socprovider = db.StringField()
    # webhook = db.StringField(default="")

    def get_status(self):
        pending = TestCase.objects(assessmentid=str(self.id),state="Pending").count()
        completed = TestCase.objects(assessmentid=str(self.id),state="Complete").count()
        total = TestCase.objects(assessmentid=str(self.id)).count()
        
        if total > 0:
            pending_percent = int((completed / total) * 100)
        else:
            pending_percent = 0
        completed_percent = 100 - pending_percent
        return {"pending": pending,
            "completed": completed,
            "total": total,
            "pending_percent": pending_percent,
            "completed_percent": completed_percent}
        

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