import json
from django.contrib.auth import get_user_model
from django.test import TestCase
from .models import Project

class IntegrationTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_superuser('example-admin', password='example-password-only')
        self.client.force_login(user)

    def test_registered_project_appears_in_menu(self):
        response = self.client.get('/admin/api/menu/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('projects.project', response.content.decode())

    def test_project_can_be_saved_with_its_document_fields(self):
        response = self.client.post('/admin/api/save/projects.project/', data=json.dumps({'data': {
            'name': '第一个项目', 'budget': '12000.50', 'status': 'draft', 'teams': [],
            'body': '<p>项目介绍</p>', 'notes': '# 协作文档\n\n', 'settings': {'enabled': True},
            'cover': '', 'attachment': '',
        }}), content_type='application/json')
        self.assertEqual(response.status_code, 200, response.content.decode())
        result = response.json()
        self.assertTrue(result['ok'], result)
        project = Project.objects.get(pk=result['data']['id'])
        self.assertEqual(str(project.budget), '12000.50')
        self.assertEqual(project.notes, '# 协作文档\n\n')
        self.assertEqual(project.settings, {'enabled': True})
