## Category: Mini-NDN

### Error: argument "peer" is wrong: "name" too long 
- **Source:** generated from Mininet . 
- e.g. Exception: Error creating interface pair (basel-eth3,mumbai_aws-eth15): Error: argument "peer" is wrong: "name" too long 
- **Solution:** shorten the name mumbai-aws to mumbai

## Category: NLSR

### error: use of undeclared identifier
../src/route/routing-table-calculator.cpp:122:8: error: use of undeclared identifier 'getNdnCxxLogger'
  if (!getNdnCxxLogger().isLevelEnabled(ndn::util::LogLevel::DEBUG)) {

- **Solution:** git pull ndn-cxx, nlsr, ChronoSync and install them. You may encounter

#### Project was configured with a different version of Waf, please reconfigure it
- **Solution:** waf configure
