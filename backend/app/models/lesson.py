from app import db


class Lesson(db.Model):
    __tablename__ = "lessons"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text)
    order = db.Column(db.Integer, default=0)

    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)

    def to_dict(self):
        return {"id": self.id, "title": self.title, "order": self.order}
