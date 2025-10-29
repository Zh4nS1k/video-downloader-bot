from typing import Optional, Dict, Any
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from config import MONGO_URI, MONGO_DB_NAME

_client: Optional[MongoClient] = None

def get_client() -> MongoClient:
	global _client
	if _client is None:
		if not MONGO_URI:
			raise RuntimeError("MONGO_URI is not set in environment")
		_client = MongoClient(MONGO_URI, uuidRepresentation="standard")
	return _client

def get_db():
	return get_client()[MONGO_DB_NAME]

def save_download(doc: Dict[str, Any]) -> None:
	try:
		db = get_db()
		doc = dict(doc)
		doc.setdefault("createdAt", datetime.utcnow())
		db.downloads.insert_one(doc)
	except PyMongoError:
		pass

def save_review(doc: Dict[str, Any]) -> None:
	try:
		db = get_db()
		doc = dict(doc)
		doc.setdefault("createdAt", datetime.utcnow())
		db.reviews.insert_one(doc)
	except PyMongoError:
		pass
