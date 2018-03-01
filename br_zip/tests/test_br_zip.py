from odoo.tests.common import TransactionCase


class TestBrZip(TransactionCase):

    def setUp(self):
        super(TestBrZip, self).setUp()

        city = self.env.ref('br_base.city_3132404')

        self.values = {
            'zip': '37503130',
            'street': 'Rua Geraldino Campista',
            'district': 'Santo Antônio',
            'city_id': city.id,
            'state_id': city.state_id.id,
            'country_id': city.state_id.country_id.id,
        }

        self.br_zip = self.env['br.zip'].create(self.values)

    def test_convert_address_fields_to_dict(self):

        res = self.br_zip.convert_address_fields_to_dict()

        self.assertIsInstance(res, dict)

        # O cep e formatado
        self.assertEqual('37503-130', res['zip'])

        self.assertEqual(self.br_zip.street, res['street'])
        self.assertEqual(self.br_zip.district, res['district'])
        self.assertEqual(self.br_zip.city_id.id, res['city_id'])
        self.assertEqual(self.br_zip.state_id.id, res['state_id'])
        self.assertEqual(self.br_zip.country_id.id, res['country_id'])

        self.assertEqual(len(res), 6)
