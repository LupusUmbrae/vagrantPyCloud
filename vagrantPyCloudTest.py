import unittest
import vagrantPyCloud

class VagrantPyCloudTest(unittest.TestCase):
    def testLegalVersion(self):
        metadata = loadMetadata()
        self.assertEqual(vagrantPyCloud.versionLegal(1, metadata, "provider"), True)
    
    def testIllegalVersion(self):
		metadata = loadMetadata()
		self.assertEqual(vagrantPyCloud.versionLegal(0, metadata, "provider"), False)

    def testIllegalProvider(self):
		metadata = loadMetadata()
		self.assertEqual(vagrantPyCloud.versionLegal(0, metadata, "testProvider"), False)


def loadMetadata():
    metadata = {}
    metadata["name"] = "test"
    metadata["description"] = "A test metadata content"
    versions = []
	
    provider_0 = {}
    provider_0["name"] = "testProvider"
    provider_0["url"] = "http://test.box"
    provider_0["checksum_type"] = "sha1"
    provider_0["checksum"] = "testSha1"
	
    version_0 = {'version':0, 'providers':[provider_0]}

    versions.insert(0, version_0)

    metadata["versions"] = versions
    return metadata

if __name__ == '__main__':
    unittest.main()
