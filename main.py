import requests
import urllib

"""
Основная логика в том, чтобы каждую строчку лога пропустить через цепочку
объектов-детекторов, каждый из которых выделит необходимы ему полезные данные и сохранит в свой буфер.
По окончании лога все детекторы начинают отправку данных в zabbix.
подводный камень - кодировка логов, в данном случае UTF-16, Сёма, привет тебе.

"""

LOG_DIRECTORY = "./logs/"
ZABBIX_HOST = "zabbix.h"
MONITORED_HOST = "1cDBHOST"

log_file_path = LOG_DIRECTORY + "log 2020-06-29.txt"

file_descriptor = open(log_file_path, "r", encoding='utf16')
log_lines = file_descriptor.readlines()
file_descriptor.close()


class Detector:
    """ Прототип детекторов, предоставляет всем наследникам свой конструктор
    regexp - подстрока, указывающая на необходимость обработки строки лога
    host - адрес сервера zabbix
    node - имя узла zabbix
    key - имя ключа элемента данных
    """
    detector_list = []

    def __init__(self, regexp, host, node, key):
        self.regexp = regexp
        self.host = host
        self.node = node
        self.key_name = key
        self.send_url = f'http://{host}/index.php?server={self.node}&key={self.key_name}&value='
        self.sending_buffer = ''
        Detector.detector_list.append(self)

    def __call__(self, log_string):
        pass

    def send_detectors_data_to_zabbix(self):
        """
        отправка собранных данных по http
        """
        http_request_result = requests.get(self.send_url + self.sending_buffer)
        print(http_request_result.text)


class MatchDetector(Detector):
    def __call__(self, log_string):
        """
        детектор собирает в се строки с указанной подстрокой и отправляет как многострочный фрагмент фрагмент текста
        """
        if self.regexp in log_string:
            self.buffer = self.buffer + urllib.parse.quote(log_string)


class SizeDetector(Detector):
    """
    Определяет размер бэкапа в байтах, заббикс сам при указании единиц переводит в
    единицы измерения большего размера.
    """

    def __call__(self, log_string):
        if self.regexp in log_string:
            splited_string = log_string.split()
            backup_size = self.convert_size_to_default_units(float(splited_string[-3].replace(",", ".")), splited_string[-2])
            self.sending_buffer = str(backup_size)

    @staticmethod
    def convert_size_to_default_units(size, units):
        """перевод единиц измерения, на вход - кол-во и едницы, на выход кол-во в байтах
        использовал 1000, а не 1024, потому что заббикс преобразовывает с 1024 самостоятельно"""
        dct = {'b': 1000, 'KB': 1000 ** 2, 'MB': 1000 ** 3, 'GB': 1000 ** 4}
        default_units = 'b'
        return size * dct[units] / dct[default_units]


class BackupTimeDetector(Detector):
    def __call__(self, log_string):
        """
        выбирает часы минуты и секунды и забирает их в буфер в виде десятичной дроби.
        """
        if self.regexp in log_string:
            splited_string = log_string.split()
            hours = splited_string[-6]
            minutes = splited_string[-4]
            seconds = splited_string[-2]
            totaltime = float(hours) + (float(minutes) / 60) + (float(seconds) / 3600)
            self.sending_buffer = str(totaltime)


MatchDetector("ERR", ZABBIX_HOST, MONITORED_HOST, 'ErrorEventHook')
SizeDetector('** Backup done for the task "54"', ZABBIX_HOST, MONITORED_HOST, 'BackupSize')
BackupTimeDetector('Total backup time for "54"', ZABBIX_HOST, MONITORED_HOST, 'TotalBackupTime')

for D_obj in Detector.detector_list:
    for line in log_lines:
        D_obj(line)

    D_obj.send_detectors_data_to_zabbix()
