from unittest import mock

from odoo.tests.common import TransactionCase


class TestCRMLead(TransactionCase):

    def setUp(self):
        super(TestCRMLead, self).setUp()
        self.crm_lead = self.env.ref('crm.crm_case_1')
        self.city = self.env.ref('br_base.city_3132404')

    @mock.patch('odoo.addons.br_zip.models.br_zip_abstract.BrZipAbstract.get_address')
    def test__onchange_zip_success(self, mk):
        cep = '37503-130'
        self.crm_lead.zip = cep
        self.crm_lead._onchange_zip()

        # Verificamos se o metodo get_address foi chamado
        self.assertEqual(mk.call_count, 1)

    @mock.patch('odoo.addons.br_zip.models.br_zip_abstract.BrZipAbstract.get_address')
    def test__onchange_zip_incorrect_zip(self, mk):
        self.crm_lead.zip = '1234567'
        self.crm_lead._onchange_zip()

        # Verificamos se o metodo get_address nao foi chamado
        # uma vez que o cep fornecido nao e valido
        self.assertEqual(mk.call_count, 0)

    def test_get_address(self):

        self.crm_lead.zip = '37503-130'
        res = self.crm_lead.get_address()

        self.assertEqual(res['zip'], '37503-130')
        self.assertEqual(res['street'], 'Rua Geraldino Campista')
        self.assertEqual(res['district'], 'Santo Antônio')
        self.assertEqual(res['city_id'], self.city.id)
        self.assertEqual(res['state_id'], self.city.state_id.id)
        self.assertEqual(res['country_id'], self.city.state_id.country_id.id)
