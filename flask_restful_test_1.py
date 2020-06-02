from flask import Flask, request
from flask_restful import Resource, Api

app = Flask(__name__)
api = Api(app)


class DemoFlaskRestful(Resource):
    def get(self):
        return {"about": "Hello World!"}

    def post(self):
        some_json = request.json
        return {"sent": some_json}, 201


class Multiply(Resource):
    def get(self, num):
        return {"result": num * 10}


api.add_resource(DemoFlaskRestful, "/")
api.add_resource(Multiply, "/multi/<int:num>")

if __name__ == "__main__":
    app.run(debug=True)

# curl -v http://127.0.0.1:5000/
# curl -H "Content-Type: application/json" -X POST -d "{\"key1\":\"value1\", \"key2\":\"value2\"}" http://127.0.0.1:5000/
# curl -v http://127.0.0.1:5000/multi/5
