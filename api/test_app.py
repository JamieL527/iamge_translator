import pytest
from flask import json
from app import app
import io

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_process_request_no_file(client):
    response = client.post('/api/process')
    assert response.status_code == 400
    assert b'No file uploaded' in response.data

def test_process_request_unsupported_file_type(client):
    data = {
        'file': (io.BytesIO(b'test content'), 'test.txt'),
        'model': 'openai',
        'selectedModel': 'gpt-4o',
        'apiKey': 'test_key',
        'language': 'en'
    }
    response = client.post('/api/process', data=data, content_type='multipart/form-data')
    assert response.status_code == 400
    assert b'Unsupported file type' in response.data

def test_process_request_unsupported_model(client):
    data = {
        'file': (io.BytesIO(b'test content'), 'test.epub'),
        'model': 'unsupported_model',
        'selectedModel': 'gpt-4o',
        'apiKey': 'test_key',
        'language': 'en'
    }
    response = client.post('/api/process', data=data, content_type='multipart/form-data')
    assert response.status_code == 400
    assert b'Unsupported model' in response.data

@pytest.mark.parametrize('file_name', ['test.epub', 'test.pdf', 'test.txt'])
def test_process_request_success(client, mocker, file_name):
    mock_book_loader = mocker.Mock()
    mock_book_loader.return_value.make_bilingual_book.return_value = None
    mocker.patch('app.BOOK_LOADER_DICT', {file_name.split('.')[-1]: mock_book_loader})
    mocker.patch('app.MODEL_DICT', {'openai': mocker.Mock()})

    data = {
        'file': (io.BytesIO(b'test content'), file_name),
        'model': 'openai',
        'selectedModel': 'gpt-4o',
        'apiKey': 'test_key',
        'language': 'en'
    }
    response = client.post('/api/process', data=data, content_type='multipart/form-data')
    assert response.status_code == 200
    assert f'Successfully processed file: {file_name}' in json.loads(response.data)['message']