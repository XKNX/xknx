import unittest

from xknx import Telegram,TelegramType,Address,TelegramDirection

class TestTelegram(unittest.TestCase):

    #
    # EQUALITY
    #
    def test_telegram_equal(self):
        self.assertEqual( Telegram(Address('1/2/3'), TelegramType.GROUP_READ), Telegram(Address('1/2/3'), TelegramType.GROUP_READ) )

    def test_telegram_not_equal(self):
        self.assertNotEqual( Telegram(Address('1/2/3'), TelegramType.GROUP_READ), Telegram(Address('1/2/4'), TelegramType.GROUP_READ) )
        self.assertNotEqual( Telegram(Address('1/2/3'), TelegramType.GROUP_READ), Telegram(Address('1/2/3'), TelegramType.GROUP_WRITE) )
        self.assertNotEqual( Telegram(Address('1/2/3'), TelegramType.GROUP_READ), Telegram(Address('1/2/3'), TelegramType.GROUP_READ, TelegramDirection.INCOMING) )

suite = unittest.TestLoader().loadTestsFromTestCase(TestTelegram)
unittest.TextTestRunner(verbosity=2).run(suite)
