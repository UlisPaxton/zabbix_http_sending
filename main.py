import requests
import urllib


LOG_DIRECTORY = "./logs/"
ZABBIX_HOST = "zab.h"
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
        self.buffer = ''
        Detector.detector_list.append(self)

    def __call__(self, log_string):
        pass

    def send_detectors_data_to_zabbix(self):
        """
        отправка собранных данных по http
        :return:
        """
        http_request_result = requests.get(self.send_url + self.buffer)
        print(http_request_result.text)


class MatchDetector(Detector):
    def __call__(self, log_string):
        """
        на вход получает строку лога, и забирает полезное к себе в буфер
        :param log_string:
        :return:
        """
        if self.regexp in log_string:
            self.buffer = self.buffer + urllib.parse.quote(log_string)


class SizeDetector(Detector):
    """
    Определяет размер бэкапа в байтах, забикс сам при указании единиц переводит в
    единицы измерения большего размера.
    """

    def __call__(self, log_string):
        if self.regexp in log_string:
            splited_string = log_string.split()
            backup_size = self.size_to_default_units(float(splited_string[-3].replace(",", ".")), splited_string[-2])
            self.buffer = str(backup_size)

    @staticmethod
    def size_to_default_units(size, units):
        """перевод единиц измерения, на вход - кол-во и едницы, на выход кол-во в байтах
        использовал 1000, а не 1024, потому что заббикс преобразовывает с 1024"""
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
            self.buffer = str(totaltime)


MatchDetector("ERR", ZABBIX_HOST, MONITORED_HOST, 'ErrorEventHook')
SizeDetector('** Backup done for the task "54"', ZABBIX_HOST, MONITORED_HOST, 'BackupSize')
BackupTimeDetector('Total backup time for "54"', ZABBIX_HOST, MONITORED_HOST, 'TotalBackupTime')

for D_obj in Detector.detector_list:
    for line in log_lines:
        D_obj(line)

    D_obj.send_detectors_data_to_zabbix()
