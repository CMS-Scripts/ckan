import json
from ckan import model
from ckan.logic.converters import convert_to_tags, convert_from_tags, free_tags_only
from ckan.lib.navl.dictization_functions import unflatten
from ckan.lib.create_test_data import CreateTestData
from ckan.tests import WsgiAppCase
from ckan.tests.functional.api import assert_dicts_equal_ignoring_ordering

class TestConverters(object):
    @classmethod
    def setup_class(cls):
        # create a new vocabulary
        cls.vocab = model.Vocabulary('test-vocab') 
        model.Session.add(cls.vocab)
        model.Session.commit()
        model.Session.remove()

    def test_convert_to_tags(self):
        def convert(tag_string, vocab):
            key = 'vocab_tag_string'
            data = {key: tag_string}
            errors = []
            context = {'model': model, 'session': model.Session}
            convert_to_tags(vocab)(key, data, errors, context)
            del data[key]
            return data

        data = unflatten(convert('tag1, tag2', 'test-vocab'))
        for tag in data['tags']:
            assert tag['name'] in ['tag1', 'tag2'], tag['name']
            assert tag['vocabulary_id'] == self.vocab.id, tag['vocabulary_id']

    def test_convert_from_tags(self):
        key = 'tags'
        data = {
            ('tags', 0, '__extras'): {'name': 'tag1', 'vocabulary_id': self.vocab.id},
            ('tags', 1, '__extras'): {'name': 'tag2', 'vocabulary_id': self.vocab.id}
        }
        errors = []
        context = {'model': model, 'session': model.Session}
        convert_from_tags(self.vocab.name)(key, data, errors, context)
        assert 'tag1' in data['tags']
        assert 'tag2' in data['tags']

    def test_free_tags_only(self):
        key = ('tags', 0, '__extras')
        data = {
            ('tags', 0, '__extras'): {'name': 'tag1', 'vocabulary_id': self.vocab.id},
            ('tags', 0, 'vocabulary_id'): self.vocab.id,
            ('tags', 1, '__extras'): {'name': 'tag2', 'vocabulary_id': None},
            ('tags', 1, 'vocabulary_id'): None
        }
        errors = []
        context = {'model': model, 'session': model.Session}
        free_tags_only(key, data, errors, context)
        assert len(data) == 2
        assert ('tags', 1, 'vocabulary_id') in data.keys()
        assert ('tags', 1, '__extras') in data.keys()

class TestAPI(WsgiAppCase):
    @classmethod
    def setup_class(cls):
        CreateTestData.create()
        cls.vocab = model.Vocabulary('test-vocab') 
        model.Session.add(cls.vocab)
        cls.vocab_tag = model.Tag('vocab-tag', cls.vocab.id)
        model.Session.add(cls.vocab_tag)
        model.Session.commit()
        model.Session.remove()

    def test_tag_list(self):
        postparams = '%s=1' % json.dumps({'vocabulary_name': self.vocab.name})
        res = self.app.post('/api/action/tag_list', params=postparams)
        body = json.loads(res.body)
        assert_dicts_equal_ignoring_ordering(
            json.loads(res.body),
            {'help': 'Returns a list of tags',
             'success': True,
             'result': [self.vocab_tag.name]}
        )

    def test_tag_list_invalid_vocab_name_404(self):
        postparams = '%s=1' % json.dumps({'vocabulary_name': 'invalid-vocab-name'})
        res = self.app.post('/api/action/tag_list', params=postparams, status=404)

