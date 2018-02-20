from unittest import TestCase

from odoo.addons.br_base.tools import fiscal


class TestFiscal(TestCase):

    def test_inscricao_estadual_ac_valida(self):
        insc_est_ac_valids = [
            '0102190200165',
            '0101296300289',
            '0100258700145',
            '0101296300106',
            '0101613200122',
            '0100662000133',
        ]

        for insc_est in insc_est_ac_valids:
            self.assertTrue(fiscal.validate_ie('ac', insc_est))

    def test_inscricao_estadual_al_valida(self):
        insc_estal_al_valids = [
            '241065550',
            '248501410',
            '240916425',
            '248540980',
            '248429981',
            '246014342',
        ]
        for insc_est in insc_estal_al_valids:
            self.assertTrue(fiscal.validate_ie('al', insc_est))

    def test_inscricao_estadual_am_valida(self):
        insc_est_am_valids = [
            '042933684',
            '041330188',
            '042357071',
            '042338964',
            '042215382',
            '042201624',
        ]
        for insc_est in insc_est_am_valids:
            self.assertTrue(fiscal.validate_ie('am', insc_est))

    def test_inscricao_estadual_ap_valida(self):

        insc_est_ap_valids = [
            '030380340',
            '030317541',
            '030273455',
            '030131818',
            '030069381',
        ]
        for insc_est in insc_est_ap_valids:
            self.assertTrue(fiscal.validate_ie('ap', insc_est))

    def test_inscricao_estadual_ba_valida(self):
        insc_est_ba_valids = [
            '41902653',
            '77893325',
            '51153771',
            '14621862',
            '09874624',
        ]
        for insc_est in insc_est_ba_valids:
            self.assertTrue(fiscal.validate_ie('ba', insc_est))

    def test_inscricao_estadual_ce_valida(self):
        insc_est_ce_valids = [
            '063873770',
            '061876640',
            '062164252',
            '061970360',
            '061880990',
            '069108595',
        ]
        for insc_est in insc_est_ce_valids:
            self.assertTrue(fiscal.validate_ie('ce', insc_est))

    def test_inscricao_estadual_df_valida(self):
        insc_est_df_valids = [
            '0732709900174',
            '0730562700176',
            '0751504400168',
            '0744409300183',
            '0748774800134',
            '0747987900103',
        ]
        for insc_est in insc_est_df_valids:
            self.assertTrue(fiscal.validate_ie('df', insc_est))

    def test_inscricao_estadual_es_valida(self):
        insc_est_es_valids = [
            '082376123',
            '082106029',
            '082467676',
            '082169713',
            '082585300',
            '082588570',
        ]
        for insc_est in insc_est_es_valids:
            self.assertTrue(fiscal.validate_ie('es', insc_est))

    def test_inscricao_estadual_go_valida(self):
        insc_est_go_valids = [
            '103450599',
            '104197633',
            '104345195',
            '104455578',
            '104555270',
        ]
        for insc_est in insc_est_go_valids:
            self.assertTrue(fiscal.validate_ie('go', insc_est))

    def test_inscricao_estadual_ma_valida(self):
        insc_est_valids = [
            '121498298',
            '122045041',
            '123214289',
            '123110130',
            '123170524',
            '121530060',
        ]
        for insc_est in insc_est_valids:
            self.assertTrue(fiscal.validate_ie('ma', insc_est))

    def test_inscricao_estadual_mg_valida(self):
        insc_est_mg_valids = [
            '7000547460067',
            '2615950220092',
            '3519900270005',
            '0621828520097',
            '5780297160005',
            '0620297160299',
        ]
        for insc_est in insc_est_mg_valids:
            self.assertTrue(fiscal.validate_ie('mg', insc_est))

    def test_inscricao_estadual_ms_valida(self):
        insc_est_valids = [
            '283370645',
            '283238933',
            '283235560',
            '283167165',
            '283267089',
            '283352124',
        ]
        for insc_est in insc_est_valids:
            self.assertTrue(fiscal.validate_ie('ms', insc_est))

    def test_inscricao_estadual_mt_valida(self):
        insc_est_valids = [
            '00133337413',
            '00133110028',
            '00132040549',
            '00133095614',
            '00132390329',
            '00131235460',
            '00132465710',
        ]
        for insc_est in insc_est_valids:
            self.assertTrue(fiscal.validate_ie('mt', insc_est))

    def test_inscricao_estadual_pa_valida(self):
        insc_est_valids = [
            '151925941',
            '152336265',
            '152355650',
            '151386358',
            '153646721',
            '152346910',
        ]
        for insc_est in insc_est_valids:
            self.assertTrue(fiscal.validate_ie('pa', insc_est))

    def test_inscricao_estadual_pb_valida(self):
        insc_est_valids = [
            '161435947',
            '161462715',
            '161455743',
            '161349242',
            '161427456',
            '160506328',
        ]
        for insc_est in insc_est_valids:
            self.assertTrue(fiscal.validate_ie('pb', insc_est))

    def test_inscricao_estadual_pr_valida(self):
        insc_est_valids = [
            '4100161414',
            '9020581252',
            '1011473551',
            '1010586972',
            '9053527172',
        ]
        for insc_est in insc_est_valids:
            self.assertTrue(fiscal.validate_ie('pr', insc_est))

    def test_inscricao_estadual_pe_valida(self):
        insc_est_valids = [
            '027693368',
            '18171203059328',
            '029748003',
            '18171001920081',
            '030374529',
        ]
        for insc_est in insc_est_valids:
            self.assertTrue(fiscal.validate_ie('pe', insc_est))

    def test_inscricao_estadual_pi_valida(self):
        insc_est_valids = [
            '169609154',
            '194549992',
            '194661059',
            '194507688',
            '194010406',
        ]
        for insc_est in insc_est_valids:
            self.assertTrue(fiscal.validate_ie('pi', insc_est))

    def test_inscricao_estadual_rj_valida(self):
        insc_est_valids = [
            '78890169',
            '78724994',
            '78205350',
            '85190881',
            '78860057',
            '78873655',
        ]
        for insc_est in insc_est_valids:
            self.assertTrue(fiscal.validate_ie('rj', insc_est))

    def test_inscricao_estadual_rn_valida(self):
        insc_est_valids = [
            '200887890',
            '200395149',
            '200653016',
            '201199351',
            '2074337760',
            '2010665163',
            '2075778442',
        ]
        for insc_est in insc_est_valids:
            self.assertTrue(fiscal.validate_ie('rn', insc_est))

    def test_inscricao_estadual_rs_valida(self):
        insc_est_valids = [
            '0240130111',
            '0963376217',
            '0290289009',
            '1240237330',
            '0570120209',
            '0962655449',
            '0962003670',
        ]
        for insc_est in insc_est_valids:
            self.assertTrue(fiscal.validate_ie('rs', insc_est))

    def test_inscricao_estadual_ro_valida(self):
        insc_est_valids = [
            '00000001656554',
            '00000001499394',
            '00000001727117',
            '00000002999277',
            '00000001765931',
        ]
        for insc_est in insc_est_valids:
            self.assertTrue(fiscal.validate_ie('ro', insc_est))

    def test_inscricao_estadual_rr_valida(self):
        insc_est_valids = [
            '240151303',
            '240042104',
            '240128125',
            '240146373',
            '240018116',
            '240106210',
            '240003910',
        ]
        for insc_est in insc_est_valids:
            self.assertTrue(fiscal.validate_ie('rr', insc_est))

    def test_inscricao_estadual_sc_valida(self):
        insc_est_valids = [
            '255830696',
            '253952662',
            '253967627',
            '254086586',
            '252625080',
            '251083110',
            '251130487',
        ]
        for insc_est in insc_est_valids:
            self.assertTrue(fiscal.validate_ie('sc', insc_est))

    def test_inscricao_estadual_sp_valida(self):
        insc_est_valids = [
            '692015742119',
            '645274188118',
            '645169551117',
            '649005952111',
            '645098352117',
        ]
        for insc_est in insc_est_valids:
            self.assertTrue(fiscal.validate_ie('sp', insc_est))

    def test_inscricao_estadual_se_valida(self):
        insc_est_valids = [
            '271126973',
            '271233648',
            '271200634',
            '270622020',
            '271307986',
        ]
        for insc_est in insc_est_valids:
            self.assertTrue(fiscal.validate_ie('se', insc_est))

    def test_inscricao_estadual_to_valida(self):
        insc_est_valids = [
            '56021275424',
            '62025717872',
            '27026857780',
            '35026423360',
        ]
        for insc_est in insc_est_valids:
            self.assertTrue(fiscal.validate_ie('to', insc_est))

    def test_inscricao_estadual_ac_invalida(self):
        insc_est_ac_valids = [
            '0102190200161',
            '0101296300282',
            '0100258700141',
            '0101296300101',
            '0101613200121',
            '0100662000131',
        ]
        for insc_est in insc_est_ac_valids:
            self.assertFalse(fiscal.validate_ie('ac', insc_est))

    def test_inscricao_estadual_al_invalida(self):
        insc_estal_al_valids = [
            '241065551',
            '248501412',
            '240916422',
            '248540982',
            '248429982',
            '246014341',
        ]
        for insc_est in insc_estal_al_valids:
            self.assertFalse(fiscal.validate_ie('al', insc_est))

    def test_inscricao_estadual_am_invalida(self):
        insc_est_am_valids = [
            '042933681',
            '041330181',
            '042357072',
            '042338961',
            '042215381',
            '042201621',
        ]
        for insc_est in insc_est_am_valids:
            self.assertFalse(fiscal.validate_ie('am', insc_est))

    def test_inscricao_estadual_ap_invalida(self):
        insc_est_ap_valids = [
            '030380341',
            '030317542',
            '030273451',
            '030131811',
            '030069385',
        ]
        for insc_est in insc_est_ap_valids:
            self.assertFalse(fiscal.validate_ie('ap', insc_est))

    def test_inscricao_estadual_ba_invalida(self):
        insc_est_ba_valids = [
            '41902652',
            '77893322',
            '51153772',
            '14621861',
            '09874625',
        ]
        for insc_est in insc_est_ba_valids:
            self.assertFalse(fiscal.validate_ie('ba', insc_est))

    def test_inscricao_estadual_ce_invalida(self):
        insc_est_ce_valids = [
            '063873771',
            '061876641',
            '062164251',
            '061970361',
            '061880991',
            '069108591',
        ]
        for insc_est in insc_est_ce_valids:
            self.assertFalse(fiscal.validate_ie('ce', insc_est))

    def test_inscricao_estadual_df_invalida(self):
        insc_est_df_valids = [
            '0732709900171',
            '0730562700171',
            '0751504400161',
            '0744409300181',
            '0748774800131',
            '0747987900101',
        ]
        for insc_est in insc_est_df_valids:
            self.assertFalse(fiscal.validate_ie('df', insc_est))

    def test_inscricao_estadual_es_invalida(self):
        insc_est_es_valids = [
            '082376121',
            '082106021',
            '082467671',
            '082169711',
            '082585301',
            '082588571',
        ]
        for insc_est in insc_est_es_valids:
            self.assertFalse(fiscal.validate_ie('es', insc_est))

    def test_inscricao_estadual_go_invalida(self):
        insc_est_go_valids = [
            '103450591',
            '104197631',
            '104345191',
            '104455571',
            '104555271',
        ]
        for insc_est in insc_est_go_valids:
            self.assertFalse(fiscal.validate_ie('go', insc_est))

    def test_inscricao_estadual_ma_invalida(self):
        insc_est_valids = [
            '121498291',
            '122045040',
            '123214281',
            '123110131',
            '123170521',
            '121530061',
        ]
        for insc_est in insc_est_valids:
            self.assertFalse(fiscal.validate_ie('ma', insc_est))

    def test_inscricao_estadual_mg_invalida(self):
        insc_est_mg_valids = [
            '2615950220091',
            '7000547460061',
            '3519900270001',
            '0621828520091',
            '5780297160001',
            '0620297160291',
        ]
        for insc_est in insc_est_mg_valids:
            self.assertFalse(fiscal.validate_ie('mg', insc_est))

    def test_inscricao_estadual_ms_invalida(self):
        insc_est_valids = [
            '283370641',
            '283238931',
            '283235561',
            '283167161',
            '283267081',
            '283352121',
        ]
        for insc_est in insc_est_valids:
            self.assertFalse(fiscal.validate_ie('ms', insc_est))

    def test_inscricao_estadual_mt_invalida(self):
        insc_est_valids = [
            '00133337411',
            '00133110021',
            '00132040541',
            '00133095611',
            '00132390321',
            '00131235461',
            '00132465711',
        ]
        for insc_est in insc_est_valids:
            self.assertFalse(fiscal.validate_ie('mt', insc_est))

    def test_inscricao_estadual_pa_invalida(self):
        insc_est_valids = [
            '151925940',
            '152336261',
            '152355651',
            '151386350',
            '153646720',
            '152346911',
        ]
        for insc_est in insc_est_valids:
            self.assertFalse(fiscal.validate_ie('pa', insc_est))

    def test_inscricao_estadual_pb_invalida(self):
        insc_est_valids = [
            '161435941',
            '161462711',
            '161455741',
            '161349241',
            '161427451',
            '160506321',
        ]
        for insc_est in insc_est_valids:
            self.assertFalse(fiscal.validate_ie('pb', insc_est))

    def test_inscricao_estadual_pr_invalida(self):
        insc_est_valids = [
            '4100161411',
            '9020581251',
            '1011473550',
            '1010586971',
            '9053527171',
        ]
        for insc_est in insc_est_valids:
            self.assertFalse(fiscal.validate_ie('pr', insc_est))

    def test_inscricao_estadual_pe_invalida(self):
        insc_est_valids = [
            '027693361',
            '18171203059321',
            '029748001',
            '18171001920080',
            '030374521',
        ]
        for insc_est in insc_est_valids:
            self.assertFalse(fiscal.validate_ie('pe', insc_est))

    def test_inscricao_estadual_pi_invalida(self):
        insc_est_valids = [
            '169609151',
            '194549991',
            '194661051',
            '194507681',
            '194010401',
        ]
        for insc_est in insc_est_valids:
            self.assertFalse(fiscal.validate_ie('pi', insc_est))

    def test_inscricao_estadual_rj_invalida(self):
        insc_est_valids = [
            '78890161',
            '78724991',
            '78205351',
            '85190880',
            '78860051',
            '78873651',
        ]
        for insc_est in insc_est_valids:
            self.assertFalse(fiscal.validate_ie('rj', insc_est))

    def test_inscricao_estadual_rn_invalida(self):
        insc_est_valids = [
            '200887891',
            '200395141',
            '200653011',
            '201199350',
            '2074337761',
            '2010665161',
            '2075778441',
        ]
        for insc_est in insc_est_valids:
            self.assertFalse(fiscal.validate_ie('rn', insc_est))

    def test_inscricao_estadual_rs_invalida(self):
        insc_est_valids = [
            '0240130110',
            '0963376211',
            '0290289001',
            '1240237331',
            '0570120201',
            '0962655441',
            '0962003671',
        ]
        for insc_est in insc_est_valids:
            self.assertFalse(fiscal.validate_ie('rs', insc_est))

    def test_inscricao_estadual_ro_invalida(self):
        insc_est_valids = [
            '00000001656551',
            '00000001499391',
            '00000001727111',
            '00000002999271',
            '00000001765930',
        ]
        for insc_est in insc_est_valids:
            self.assertFalse(fiscal.validate_ie('ro', insc_est))

    def test_inscricao_estadual_rr_invalida(self):
        insc_est_valids = [
            '240151301',
            '240042101',
            '240128121',
            '240146371',
            '240018111',
            '240106211',
            '240003911',
        ]
        for insc_est in insc_est_valids:
            self.assertFalse(fiscal.validate_ie('rr', insc_est))

    def test_inscricao_estadual_sc_invalida(self):
        insc_est_valids = [
            '255830691',
            '253952661',
            '253967621',
            '254086581',
            '252625081',
            '251083111',
            '251130481',
        ]
        for insc_est in insc_est_valids:
            self.assertFalse(fiscal.validate_ie('sc', insc_est))

    def test_inscricao_estadual_sp_invalida(self):
        insc_est_valids = [
            '692015742111',
            '645274188111',
            '645169551111',
            '649005952110',
            '645098352111',
        ]
        for insc_est in insc_est_valids:
            self.assertFalse(fiscal.validate_ie('sp', insc_est))

    def test_inscricao_estadual_se_invalida(self):
        insc_est_valids = [
            '271126971',
            '271233641',
            '271200631',
            '270622021',
            '271307981',
        ]
        for insc_est in insc_est_valids:
            self.assertFalse(fiscal.validate_ie('se', insc_est))

    def test_inscricao_estadual_to_invalida(self):
        insc_est_valids = [
            '56021275421',
            '62025717871',
            '27026857781',
            '35026423361',
        ]
        for insc_est in insc_est_valids:
            self.assertFalse(fiscal.validate_ie('to', insc_est))
