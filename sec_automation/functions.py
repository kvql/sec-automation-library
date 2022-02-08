import ipaddress
import re
import json
import defusedxml.ElementTree as ET
import logging
from sys import exit

import logging
logger= logging.getLogger(__name__)

netIP1 = re.compile('^([0-9]{1,3}\.){3}3$')
netIP2 = re.compile('^([0-9]{1,3}\.){3}255$')


rgxIP = re.compile('^([0-9]{1,3}\.){3}[0-9]{1,3}$')
rgxRng = re.compile('^([0-9]{1,3}\.){3}[0-9]{1,3}-([0-9]{1,3}\.){3}[0-9]{1,3}$')


loggers = {}

def create_logger(name:str,log_level:str, log_file=None):
    global loggers

    if loggers.get(name):
        return loggers.get(name)
    else:
        logger = logging.getLogger(name)

        if log_level == "DEBUG":
            log_level = logging.DEBUG
        elif log_level == "ERROR":
            log_level = logging.ERROR
        elif log_level == "WARN":
            log_level = logging.WARN
        else:
            log_level = logging.INFO

        if log_file != None:
            fh = logging.FileHandler(log_file, mode='a') # file handler
            fh.setLevel(log_level)

            # Set formatter for each handler
            formatter = logging.Formatter('%(asctime)s, %(levelname)s, %(name)s, %(message)s')
            fh.setFormatter(formatter)
            logger.addHandler(fh)
        
        logger.setLevel(log_level)

        # create console and file handler and set level
        ch = logging.StreamHandler() # console handler
        ch.setLevel(log_level)

        formatter = logging.Formatter('%(levelname)s - %(name)s -  %(message)s') 
        ch.setFormatter(formatter) # add formatter

        # add ch & fh to logger
        logger.addHandler(ch)
        loggers[name] = logger

        return logger

def is_ipv4(item:str):
    if re.match(rgxIP,item):
        return True
    else:
        return False

def compare_dict(item1:dict, item2:dict):
    item1_list = list(item1.keys())
    if len(item1_list)==1:
        item1_str = str(item1_list)
    elif len(item1_list) >1:
        item1_str = str(item1_list.sort())
    else:
        logger.debug("unexpected list comparison")
        return False
    item2_list = list(item2.keys())
    if len(item2_list)==1:
        item2_str = str(item2_list)
    elif len(item2_list) >1:
        item2_str = str(item2_list.sort())
    else:
        logger.debug("unexpected list comparison")
        return False
    if item1_str == item2_str:
        return True
    else:
        return False

def compare_list(item1_list:dict, item2_list:dict):
    if len(item1_list)==1:
        item1_str = str(item1_list)
    elif len(item1_list) >1:
        item1_str = str(item1_list.sort())
    else:
        logger.debug("unexpected list comparison")
        return False

    if len(item2_list)==1:
        item2_str = str(item2_list)
    elif len(item2_list) >1:
        item2_str = str(item2_list.sort())
    else:
        logger.debug("unexpected list comparison")
        return False
    if item1_str == item2_str:
        return True
    else:
        return False

def validate_dns(dns:str):
    dns = dns.strip('*.')
    if dns[-1] == ".":
        dns = dns[:-1]
    return dns


def is_json(myjson):
    try:
        json_object = json.loads(myjson)
    except ValueError as e:
        return False
    return True

def return_json(myjson):
    if is_json(myjson):
        return json.loads(myjson)
    else:
        raise Exception("value not json")

def csvparse(path):
    file = open(path, 'r')
    subnets = []
    for line in file:
        line = line.split(',')
        if re.match(rgxIP, line[1]):
            subnets.append(RawIpamSubnet(line))

    return subnets
def is_int(s):
    try: 
        int(s)
        return True
    except ValueError:
        return False


def dataHandler(local:bool):
    if local:
        path="/tmp/"
        open


#TODO
# import list of excluded subnets and reasons for exclusion


def compileReport(RawIpamList: list, assetgroups: list):
    i = 0
    report = CoverageReport()
    # loop to go through subnets from IPAM and identify, empty subnets, subnets with coverage and subnets without
    # coverage
    # Subnets with coverage will have overall coverage % and coverage % for each asset group
    while i < len(RawIpamList):
        if RawIpamList[i].IPsUsed == 0:
            report.numEmptySubnets += 1
            RawIpamList.pop(i)
        else:
            if RawIpamList[i].IPsUsed <= 3 and not RawIpamList[i].public:
                report.numPotentiallyEmptySubnets += 1
            else:
                report.numUsedSubnets += 1
            RawIpamList[i].evalcoverage(assetgroups)  # return subnet with list of indexes to asset groups that cover a
            # % of this subnet
            if RawIpamList[i].coverage:
                RawIpamList[i].evaloverlap(assetgroups)  # for each index asset group with coverage of this subnet
                # evaluate the % coverage and the combined coverage
                report.CoveredSubnets.append(RawIpamList[i])
                i += 1
            else:
                if RawIpamList[i].IPsUsed <= 3:
                    report.nonCovSubLt3IP += 1
                report.nonCoveredSubnets.append(RawIpamList[i])
                RawIpamList.pop(i)
    i = 0
    while i < len(assetgroups):
        x = 0
        report.AGCoverageList.append(AGCoverage(assetgroups[i]))
        for subnet in report.CoveredSubnets:
            if assetgroups[i].name in subnet.AGandCoverage[0]:
                x += 1
                report.AGCoverageList[i].rawSubnets.append(subnet)
        report.AGCoverageList[i].numSubnets = x
        i += 1
    report.meancoverage(RawIpamList)
    return report

# class for store enriched info about a subnet
# 
class RawIpamSubnet:
    def __init__(self, line: list):
        self.name = line[0]
        self.subnet = ipaddress.ip_network(line[1] + '/' + line[2])
        self.IPsUsed = int(line[5].split(" ")[0])
        self.coverage = False
        self.overallCoverage = 0.0
        self.AGsWithCoverage = []
        self.AGsWithMatchingSupernet = []
        self.AGandCoverage = [[], []]
        self.public = not self.subnet.is_private

    def evalcoverage(self,assetgroups: list):
        if self.IPsUsed != 0:
            i = 0
            self.AGsWithCoverage = []
            for x in assetgroups:  # loop through asset groups
                check = False
                for vuln_scannerSubnet in x.AG_Ranges:
                    if vuln_scannerSubnet.overlaps(self.subnet):
                        self.coverage = True
                        check = True
                        self.AGsWithCoverage.append(i)
                        break
                if not check:
                    for ip in x.AG_IPs:
                        if ip in self.subnet:
                            self.coverage = True
                            self.AGsWithCoverage.append(i)
                            break
                i += 1
            if not self.coverage:
                self.evalSupernet(assetgroups)


    def evalSupernet(self, assetgroups: list):
        self.AGsWithMatchingSupernet = []
        rawSupernet = self.subnet.supernet(new_prefix=16)
        for ag in assetgroups:
            if rawSupernet == ag.AG_superset:
                self.AGsWithMatchingSupernet.append(ag.name)

    def evaloverlap(self, assetgroups: list):
        numIPs = self.subnet.num_addresses
        subnet_ips = []
        for addr in self.subnet:
            subnet_ips.append(addr)
        subnet_ips2 = subnet_ips.copy()
        subnet_ips_control = subnet_ips.copy()
        if len(self.AGsWithCoverage) > 0:
            for idx in self.AGsWithCoverage:
                subnet_ips = subnet_ips_control.copy()
                i = 0
                while i < len(subnet_ips):
                    ip = subnet_ips[i]
                    if ip in assetgroups[idx].AG_IPs:
                        subnet_ips.remove(ip)
                        if ip in subnet_ips2:
                            subnet_ips2.remove(ip)
                    else:
                        check = True
                        for agrange in assetgroups[idx].AG_Ranges:
                            if ip in agrange:
                                subnet_ips.remove(ip)
                                check = False
                                i2 = 0
                                while i2 < len(subnet_ips): #AS this range contains an IP loop trough all ip for this range to speed up search
                                    if subnet_ips[i2] in agrange:
                                        if subnet_ips[i2] in subnet_ips2:
                                            subnet_ips2.remove(subnet_ips[i2])
                                        subnet_ips.remove(subnet_ips[i2])
                                    else:
                                        i2 += 1
                                if ip in subnet_ips2:
                                    subnet_ips2.remove(ip)
                                break
                        if check:
                            i += 1

                self.AGandCoverage[0].append(assetgroups[idx].name)
                self.AGandCoverage[1].append((numIPs-len(subnet_ips))/numIPs*100)
            self.overallCoverage = (numIPs-len(subnet_ips2))/numIPs*100


class CoverageReport:
    def __init__(self):
        self.AGCoverageList = []
        self.numEmptySubnets = 0
        self.numPotentiallyEmptySubnets = 0
        self.numUsedSubnets = 0
        self.nonCoveredSubnets = [] # list of RawIpamSubnet objects
        self.nonCovSubLt3IP = 0
        self.CoveredSubnets = []
        self.averageCoverage = 0.0 # mean coverage excluding subnets without
        self.agswithoverlap = 0

    def printreport(self):
        print("#" * 24 + "\nAsset Group Coverage\n" + "#" * 24)
        for ag in self.AGCoverageList:
            print("\n" + "~" * 20 + "\nName: " + ag.name + "\n# of subnets: " + str(ag.numSubnets) + "\n" + "~" * 20)
            if ag.numSubnets > 0:
                print("IPAM Range\t|\t% Coverage\t|\tOverlapping Asset Groups\t|\t% Coverage (Including Overlap)")
                for subnet in ag.rawSubnets:
                    groupnames = list(subnet.AGandCoverage[0])
                    coverage = 0.0
                    i = 0
                    while i < len(groupnames):
                        if ag.name == groupnames[i]:
                            coverage = subnet.AGandCoverage[1][i]
                            groupnames.pop(i)
                        else:
                            i += 1
                    line = str(subnet.subnet) + "\t|\t" + str(coverage) + "\t|\t" + str(groupnames) + "\t|\t" + str(subnet.overallCoverage)
                    print(line)
        print("\n\n" + "#" * 24 + "\nSubnets with No Coverage\n" + "#" * 24)
        print("Subnet\t|\tUsed IPs\t|\tAGs with Matching Supernet\n" + "_" * 50)
        for subnet in self.nonCoveredSubnets:
            line = str(subnet.subnet) + "\t|\t" + str(subnet.IPsUsed) + "\t|\t" + str(subnet.AGsWithMatchingSupernet)
            print(line)
        print("\n\n" + "#" * 24 + "\nSummary\n" + "#" * 24)
        print("Average AG Coverage:\t" + str(self.averageCoverage))
        print("Number of empty subnets excluded from reporting:\t|\t" + str(self.numEmptySubnets))
        print("Number of subnets with <= 3 used IPs:\t|\t" + str(self.numPotentiallyEmptySubnets))
        print("Number of subnets with > 3 used IPs:\t|\t" + str(self.numUsedSubnets))
        print("Number of Covered subnets:\t|\t" + str(len(self.CoveredSubnets)))
        print("Number of non Covered subnets:\t|\t" + str(len(self.nonCoveredSubnets)))
        print("Number of non Covered subnets with <= 3 IPs:\t|\t" + str(self.nonCovSubLt3IP))

    def printreportcsv(self):
        #print("#" * 24 + "\nAsset Group Coverage\n" + "#" * 24)
        print("subnet, IPs Used, Overall Coverage, public, AGs with Coverage")
        for subnet in self.CoveredSubnets:
            line  = str(subnet.subnet) + ", " + str(subnet.IPsUsed) + ", " + str(subnet.overallCoverage) +"%, " + str(subnet.public) + ", " + str(subnet.AGsWithCoverage)
            print(line)

    def meancoverage(self, subnets):
        temp = []
        for sub in subnets:
            temp.append(sub.overallCoverage)
        self.averageCoverage = sum(temp)/len(temp)


# ToDO convert below class to json
class AGCoverage:
    def __init__(self, ag):
        self.name = ag.name
        self.numSubnets = 0
        self.rawSubnets = []  # list of IpamList ohjects that overlap with ag


class ParsedAG:
    def __init__(self, ag):
        self.AG_IPs = []
        self.AG_Ranges = []
        self.name = ag.title
        self.AG_superset = ipaddress.IPv4Network
        for x in ag.scanips:
            x = x.text  # x by default is string element. This extract just the string
            if re.match(rgxIP, x):
                self.AG_IPs.append(ipaddress.IPv4Address(x))
            elif re.match(rgxRng, x):
                y = x.split('-')
                y[0] = ipaddress.IPv4Address(y[0])
                y[1] = ipaddress.IPv4Address(y[1])
                for z in [ipaddr for ipaddr in ipaddress.summarize_address_range(y[0], y[1])]:
                    self.AG_Ranges.append(z)
        i = 0
        while i < len(self.AG_Ranges):
            if self.AG_Ranges[i].num_addresses < 16:
                for ip in self.AG_Ranges[i]:
                    self.AG_IPs.append(ip)
                self.AG_Ranges.pop(i)
            else:
                i += 1
        self.superset()

    #TODO
    # increase accuracy of this function
    def superset(self): # function needs refinement
        try:
            if len(self.AG_Ranges) > 0: # find the /16 supernet of ranges if asset group covers more than 1 /16 range this will not work
                self.AG_superset = self.AG_Ranges[0].supernet(new_prefix=16)
                for iprange in self.AG_Ranges:
                    if self.AG_superset != iprange.supernet(new_prefix=16) and not self.AG_superset.supernet_of(iprange.supernet(new_prefix=16)) and self.AG_superset.supernet(new_prefix=16).supernet_of(self.AG_superset):
                        self.AG_superset = self.AG_superset.supernet(new_prefix=16)
            elif len(self.AG_IPs) >0: # not fully accurate but give estimate of supernet of single IPs in asset group
                for z in [ipaddr for ipaddr in ipaddress.summarize_address_range(self.AG_IPs[0], self.AG_IPs[len(self.AG_IPs)-1])]:
                    self.AG_superset = z.supernet(new_prefix=16)
                    break
        except:
                print("error:"+str(self.AG_superset))

