import os
import requests
import json
from urllib.parse import quote

class FirebaseClient:
    def __init__(self, id_token=None):
        self.project_id = os.getenv("FIREBASE_PROJECT_ID")
        self.base_url = f"https://firestore.googleapis.com/v1/projects/{self.project_id}/databases/(default)/documents"
        self.api_key = os.getenv("FIREBASE_API_KEY")
        self.id_token = id_token
    
    def get_collection(self, collection_name):
        """Fetch all documents from a collection"""
        url = f"{self.base_url}/{collection_name}?key={self.api_key}"
        headers = {}
        if self.id_token:
            headers["Authorization"] = f"Bearer {self.id_token}"
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        documents = []
        if 'documents' in data:
            for doc in data['documents']:
                doc_id = doc['name'].split('/')[-1]
                fields = self._parse_fields(doc.get('fields', {}))
                fields['id'] = doc_id
                documents.append(fields)
        
        return documents
    
    def get_document(self, collection_name, doc_id):
        """Fetch a single document by ID"""
        url = f"{self.base_url}/{collection_name}/{doc_id}?key={self.api_key}"
        headers = {}
        if self.id_token:
            headers["Authorization"] = f"Bearer {self.id_token}"
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        doc = response.json()
        
        fields = self._parse_fields(doc.get('fields', {}))
        fields['id'] = doc_id
        return fields
    
    def query_collection(self, collection_name, field, operator, value):
        """
        Query a collection in Firebase with a filter
        Returns: list of documents
        """
        try:
            # Use the structured query format required by Firestore REST API
            url = f"{self.base_url}:runQuery?key={self.api_key}"
            
            # Format the query with proper Firestore syntax
            payload = {
                "structuredQuery": {
                    "from": [{"collectionId": collection_name}],
                    "where": {
                        "fieldFilter": {
                            "field": {"fieldPath": field},
                            "op": self._convert_operator(operator),
                            "value": self._to_firebase_value(value)
                        }
                    }
                }
            }
            
            headers = {"Content-Type": "application/json"}
            if self.id_token:
                headers["Authorization"] = f"Bearer {self.id_token}"
            
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            # Parse the response - Firestore returns an array of document objects
            data = response.json()
            documents = []
            
            for item in data:
                if "document" in item:
                    doc = item["document"]
                    doc_id = doc["name"].split("/")[-1]
                    fields = self._parse_fields(doc.get("fields", {}))
                    fields["id"] = doc_id
                    documents.append(fields)
                    
            return documents
            
        except Exception as e:
            print(f"Firebase query error: {str(e)}")
            raise e
    
    def create_document(self, collection_name, doc_id, data):
        """Create or update a document with a specific ID"""
        url = f"{self.base_url}/{collection_name}/{doc_id}?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        if self.id_token:
            headers["Authorization"] = f"Bearer {self.id_token}"
        
        firebase_data = {"fields": self._to_firebase_fields(data)}
        response = requests.patch(url, json=firebase_data, headers=headers)
        response.raise_for_status()
        return response.json()
    
    def query_collection_with_filters(self, collection, filters):
        """
        Query a collection with multiple filters
        
        Args:
            collection: Collection name
            filters: List of tuples in the format (field, operator, value)
            
        Returns:
            List of matching documents
        """
        try:
            # Use the runQuery endpoint instead of URL parameters
            url = f"{self.base_url}:runQuery?key={self.api_key}"
            
            # Build a structured query with filters
            filter_objects = []
            for field, op, value in filters:
                filter_objects.append({
                    "fieldFilter": {
                        "field": {"fieldPath": field},
                        "op": self._convert_operator(op),
                        "value": self._to_firebase_value(value)
                    }
                })
            
            # Combine filters with AND logic
            filter_section = {}
            if len(filter_objects) == 1:
                filter_section = filter_objects[0]
            elif len(filter_objects) > 1:
                filter_section = {
                    "compositeFilter": {
                        "op": "AND",
                        "filters": filter_objects
                    }
                }
            
            # Construct the full query
            payload = {
                "structuredQuery": {
                    "from": [{"collectionId": collection}],
                    "where": filter_section
                }
            }
            
            # Make the request
            headers = {"Content-Type": "application/json"}
            if self.id_token:
                headers["Authorization"] = f"Bearer {self.id_token}"
                
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            # Parse the response
            data = response.json()
            
            # Convert Firebase format to simple dictionaries
            result = []
            for item in data:
                if "document" in item:
                    doc = item["document"]
                    doc_id = doc["name"].split("/")[-1]
                    fields = doc.get("fields", {})
                    
                    # Convert Firestore field types to Python types
                    doc_data = {"id": doc_id}
                    doc_data.update(self._parse_fields(fields))
                    result.append(doc_data)
            
            return result
            
        except Exception as e:
            print(f"Error querying collection: {str(e)}")
            # Return empty list instead of raising to prevent UI crashes
            return []
    
    def _convert_operator(self, operator):
        """Convert Python-style operators to Firebase operators"""
        operators = {
            "==": "EQUAL",
            ">": "GREATER_THAN",
            "<": "LESS_THAN",
            ">=": "GREATER_THAN_OR_EQUAL",
            "<=": "LESS_THAN_OR_EQUAL"
        }
        return operators.get(operator, "EQUAL")
    
    def _to_firebase_value(self, value):
        """Convert a Python value to Firebase value format"""
        if isinstance(value, str):
            return {"stringValue": value}
        elif isinstance(value, int):
            return {"integerValue": str(value)}
        elif isinstance(value, float):
            return {"doubleValue": value}
        elif isinstance(value, bool):
            return {"booleanValue": value}
        elif value is None:
            return {"nullValue": None}
        else:
            return {"stringValue": str(value)}
    
    def _to_firebase_fields(self, data):
        """Convert a Python dict to Firebase fields format"""
        fields = {}
        for key, value in data.items():
            if isinstance(value, dict):
                fields[key] = {"mapValue": {"fields": self._to_firebase_fields(value)}}
            else:
                fields[key] = self._to_firebase_value(value)
        return fields
    
    def _parse_fields(self, firebase_fields):
        """Parse Firebase fields format to Python dict"""
        result = {}
        for key, value_obj in firebase_fields.items():
            for type_name, value in value_obj.items():
                if type_name == 'stringValue':
                    result[key] = value
                elif type_name == 'integerValue':
                    result[key] = int(value)
                elif type_name == 'doubleValue':
                    result[key] = float(value)
                elif type_name == 'booleanValue':
                    result[key] = bool(value)
                elif type_name == 'nullValue':
                    result[key] = None
                elif type_name == 'mapValue':
                    result[key] = self._parse_fields(value.get('fields', {}))
                elif type_name == 'arrayValue':
                    result[key] = [self._parse_value(item) for item in value.get('values', [])]
        return result
    
    def _parse_value(self, value_obj):
        """Parse a single Firebase value to Python value"""
        if not value_obj:
            return None
        
        for type_name, value in value_obj.items():
            if type_name == 'stringValue':
                return value
            elif type_name == 'integerValue':
                return int(value)
            elif type_name == 'doubleValue':
                return float(value)
            elif type_name == 'booleanValue':
                return bool(value)
            elif type_name == 'nullValue':
                return None
            elif type_name == 'mapValue':
                return self._parse_fields(value.get('fields', {}))
        return None
