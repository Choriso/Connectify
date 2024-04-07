from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///interests.db'  # Используем SQLite базу данных
db = SQLAlchemy(app)

class Interest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    description = db.Column(db.Text)
    tags = db.Column(db.String(100))

    def __repr__(self):
        return f'<Interest {self.title}>'

@app.route('/add_interest', methods=['POST'])
def add_interest():
    data = request.get_json()
    title = data['title']
    description = data['description']
    tags = data['tags']

    new_interest = Interest(title=title, description=description, tags=tags)
    db.session.add(new_interest)
    db.session.commit()
    return jsonify({'message': 'Interest added successfully!'}), 201

@app.route('/get_interests', methods=['GET'])
def get_interests():
    interests = Interest.query.all()
    interest_list = []
    for interest in interests:
        interest_data = {'title': interest.title,
                         'description': interest.description,
                         'tags': interest.tags}
        interest_list.append(interest_data)
    return jsonify({'interests': interest_list}), 200

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)