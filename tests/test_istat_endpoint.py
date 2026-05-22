import unittest
import xml.etree.ElementTree as ET

import certifi
import requests


class IstatEndpointTest(unittest.TestCase):
    def test_istat_dataflow_endpoint_is_reachable(self):
        url = "https://esploradati.istat.it/SDMXWS/rest/dataflow/IT1/169_745/latest"

        response = requests.get(url, timeout=20, verify=certifi.where())

        self.assertLess(response.status_code, 400, response.text[:500])
        self.assertTrue(response.content)

        try:
            root = ET.fromstring(response.content)
        except ET.ParseError as exc:
            self.fail(f"ISTAT endpoint did not return valid XML: {exc}")

        self.assertTrue(root.tag.endswith("Structure"), root.tag)


if __name__ == "__main__":
    unittest.main()
