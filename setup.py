import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="sec-automation", # Replace with your own username
    version="1.1.1",
    author="Kevin Quill",
    author_email="",
    description="package of common functions and objects used for automating secuity operation tasks",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="",
    packages=["sec_automation",
    "sec_automation/integrations"],
    install_requires=[
    "python-tss-sdk", 
    "google-cloud-storage",
    "google-cloud-secret-manager", 
    "google-api-python-client", 
    "defusedxml",
    "ipaddress", 
    "lxml", 
    "pytest",
    "requests",
    "google-cloud-dns",
    "google-cloud-resource-manager",
    "google-cloud-securitycenter",
    "azure-mgmt-subscription",
    "azure-mgmt-network",
    "azure-identity"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
