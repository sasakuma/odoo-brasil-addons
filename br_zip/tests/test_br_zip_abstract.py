from unittest import mock

from pycep_correios.excecoes import (CEPInvalido,
                                     ExcecaoPyCEPCorreios,
                                     FalhaNaConexao)
from pycep_correios import HOMOLOGACAO

from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError


class TestBrZipAbstract(TransactionCase):

    def setUp(self):
        super(TestBrZipAbstract, self).setUp()

    def test_get_address_from_zip_success(self):

        with mock.patch('odoo.addons.br_zip.models.br_zip_abstract.consultar_cep') as mk:
            mk.return_value = {
                'cep': '37503130',
                'end': 'Rua Geraldino Campista',
                'bairro': 'Santo Antônio',
                'cidade': 'Itajubá',
                'uf': 'MG',
            }

            res = self.env['br.zip.abstract'].get_address_from_zip('zzz',
                                                                   environment=HOMOLOGACAO)

            self.assertEqual(res['zip_code'], '37503130')
            self.assertEqual(res['street'], 'Rua Geraldino Campista')
            self.assertEqual(res['district'], 'Santo Antônio')
            self.assertEqual(res['city'], 'Itajubá')
            self.assertEqual(res['state_code'], 'MG')
            self.assertEqual(res['country_code'], 'BR')

            mk.assert_called_once_with('zzz', ambiente=HOMOLOGACAO)

    @mock.patch('odoo.addons.br_zip.models.br_zip_abstract.consultar_cep')
    def test_get_address_from_zip_cep_invalido(self, mk):

        mk.side_effect = CEPInvalido()

        with self.assertRaises(UserError):
            self.env['br.zip.abstract'].get_address_from_zip('37503130',
                                                             environment=HOMOLOGACAO)

    @mock.patch('odoo.addons.br_zip.models.br_zip_abstract.consultar_cep')
    def test_get_address_from_zip_falha_conexao(self, mk):

        mk.side_effect = FalhaNaConexao()

        with self.assertRaises(UserError):
            self.env['br.zip.abstract'].get_address_from_zip('37503130',
                                                             environment=HOMOLOGACAO)

    @mock.patch('odoo.addons.br_zip.models.br_zip_abstract.consultar_cep')
    def test_get_address_from_zip_excecao_pycepcorreios(self, mk):

        mk.side_effect = ExcecaoPyCEPCorreios()

        with self.assertRaises(UserError):
            self.env['br.zip.abstract'].get_address_from_zip('37503130',
                                                             environment=HOMOLOGACAO)

    def test_create_br_zip_from_address(self):

        values = {
            'zip_code': '37503130',
            'street': 'Rua Geraldino Campista',
            'district': 'Santo Antônio',
            'city': 'Itajubá',
            'state_code': 'MG',
            'country_code': 'BR',
        }

        br_zip = self.env['br.zip.abstract'].create_br_zip_from_address(
            **values)

        self.assertEqual(br_zip._name, 'br.zip')

        self.assertEqual(br_zip.zip, '37503130')
        self.assertEqual(br_zip.street, 'Rua Geraldino Campista')
        self.assertEqual(br_zip.district, 'Santo Antônio')
        self.assertEqual(br_zip.city_id.name, 'Itajubá')
        self.assertEqual(br_zip.state_id.code, 'MG')
        self.assertEqual(br_zip.country_id.code, 'BR')
