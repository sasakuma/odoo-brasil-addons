from pycep_correios import HOMOLOGACAO

from odoo.tests.common import TransactionCase


class TestBrZipAbstract(TransactionCase):

    def setUp(self):
        super(TestBrZipAbstract, self).setUp()

    def test_get_address_from_zip_code(self):

        res = self.env['br.zip.abstract'].get_address_from_zip(zip_code='37503130',
                                                               environment=HOMOLOGACAO)

        self.assertEqual(res['zip_code'], '37503130')
        self.assertEqual(res['street'], 'Rua Geraldino Campista')
        # self.assertEqual(res['street_type'], '')
        self.assertEqual(res['district'], 'Santo Antônio')
        self.assertEqual(res['city'], 'Itajubá')
        self.assertEqual(res['state_code'], 'MG')
        self.assertEqual(res['country_code'], 'BR')

    def test_create_br_zip_from_address(self):

        values = {
            'zip_code': '37503130',
            'street': 'Rua Geraldino Campista',
            # 'street_type': 'XPTO',
            'district': 'Santo Antônio',
            'city': 'Itajubá',
            'state_code': 'MG',
            'country_code': 'BR',
        }

        br_zip = self.env['br.zip.abstract'].create_br_zip_from_address(**values)

        self.assertEqual(br_zip._name, 'br.zip')

        self.assertEqual(br_zip.zip, '37503130')
        self.assertEqual(br_zip.street, 'Rua Geraldino Campista')
        # self.assertEqual(br_zip.street_type, 'XPTO')
        self.assertEqual(br_zip.district, 'Santo Antônio')
        self.assertEqual(br_zip.city_id.name, 'Itajubá')
        self.assertEqual(br_zip.state_id.code, 'MG')
        self.assertEqual(br_zip.country_id.code, 'BR')
