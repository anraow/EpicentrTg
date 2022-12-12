import pymongo


class Auth:
    def __init__(self):
        self.client = pymongo.MongoClient(host=['localhost:27017'], document_class=dict, tz_aware=False, connect=True)
        self.db = self.client['bot']
        self.collection = self.db['users']

    def create_document(self, doc):
        self.collection.insert_one(doc)

    def check_user_exist(self, u_id):
        res = self.collection.find_one({"user_id": int(u_id)})
        return res

    def close(self):
        self.client.close()
