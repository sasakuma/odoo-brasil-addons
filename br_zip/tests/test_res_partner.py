from unittest import mock

from odoo.tests.common import TransactionCase


class TestResPartner(TransactionCase):

    def setUp(self):
        super(TestResPartner, self).setUp()
        self.partner = self.env.ref('base.res_partner_2')
        self.city = self.env.ref('br_base.city_3132404')

    @mock.patch('odoo.addons.br_zip.models.br_zip_abstract.BrZipAbstract.get_address')
    def test__onchange_zip_success(self, mk):
        cep = '37503-130'
        self.partner.zip = cep
        self.partner._onchange_zip()

        # Verificamos se o metodo get_address foi chamado
        self.assertEqual(mk.call_count, 1)

    @mock.patch('odoo.addons.br_zip.models.br_zip_abstract.BrZipAbstract.get_address')
    def test__onchange_zip_incorrect_zip(self, mk):
        self.partner.zip = '1234567'
        self.partner._onchange_zip()

        # Verificamos se o metodo get_address nao foi chamado
        # uma vez que o cep fornecido nao e valido
        self.assertEqual(mk.call_count, 0)

    def test_get_address(self):

        self.partner.zip = '37503-130'
        res = self.partner.get_address()

        self.assertEqual(res['zip'], '37503-130')
        self.assertEqual(res['street'], 'Rua Geraldino Campista')
        self.assertEqual(res['district'], 'Santo Antônio')
        self.assertEqual(res['city_id'], self.city.id)
        self.assertEqual(res['state_id'], self.city.state_id.id)
        self.assertEqual(res['country_id'], self.city.state_id.country_id.id)
