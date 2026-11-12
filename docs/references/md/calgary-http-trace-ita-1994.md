---
# --- bibliographic record ---
entry_type: misc
title: "Calgary-HTTP trace"
authors:
  - "Internet Traffic Archive"
year: 1994
venue: "Internet Traffic Archive, Lawrence Berkeley National Laboratory"
volume: ""
issue: ""
pages: ""
publisher: ""
doi: ""
arxiv: ""
url: "https://ita.ee.lbl.gov/html/contrib/Calgary-HTTP.html"

# --- archive record ---
source_pdf: calgary-http-trace-ita-1994.pdf
source_sha256: 61fbe14c13409c1db44af072aad72fe8e56f5eb0c6e35d38efbed75ae17824a8
pdf_pages: 1
converted: 2026-11-12
record_source: manual
review: "web page printed to PDF on 2026-11-12; the log runs 24 October 1994 to 11 October 1995; trace contributed by Martin Arlitt and Carey Williamson"
key_insight: "About one year of requests, 24 October 1994 to 11 October 1995, 726,739 requests to the University of Calgary computer science web server. Contributed by Martin Arlitt and Carey Williamson."
first_page: "Calgary-HTTP Description This trace contains approximately one year's worth of all HTTP requests to the University of Calgary's Department of Computer Science WWW server located at Calgary, Alberta, C"
---
# **_Calgary-HTTP_** 

## **Description** 

This trace contains approximately one year's worth of all HTTP requests to the University of Calgary's Department of Computer Science WWW server located at Calgary, Alberta, Canada. 

## **Format** 

The logs are an ASCII file with one line per request, with the following columns: 

1. **host** making the request. Hosts are identified as either **local** or **remote** where **local** is a host from the University of Calgary, and **remote** is a host from outside of the University of Calgary domain. 

2. **timestamp** in the format "DAY MON DD HH:MM:SS YYYY", where **DAY** is the day of the week, **MON** is the name of the month, **DD** is the day of the month, **HH:MM:SS** is the time of day using a 24-hour clock, and **YYYY** is the year. The timezone is -0700 between 30/Oct/1994:01:30:57 and 02/Apr/1995:03:03:26. For all other requests, the timezone is -0600. 

3. **filename** of the requested item. Paths have been removed. Modified filenames consist of two parts: **num.type** , where **num** is a unique integer identifier, and **type** is the extension of the requested file. 

4. **HTTP reply code** . 

5. **bytes in the reply** . 

## **Measurement** 

The logs were collected from October 24, 1994 through October 11, 1995, a total of 353 days. There were 726,739 requests. Timestamps have 1 second resolution. 

## **Privacy** 

The sites making requests to the server have had their addresses removed to preserve privacy. Paths have been removed. Files were numbered from 1 for the first file encountered in the trace. Files retain the original file extension, so that the type of file can be determined. 

## **Acknowledgements** 

The logs were collected by Robert Fridman of the University of Calgary Department of Computer Science, and contributed by Martin Arlitt ( _mfa126@cs.usask.ca_ ) and Carey Williamson ( _carey@cs.usask.ca_ ) of the University of Saskatchewan. 

## **Publications** 

This is one of six data sets analyzed in an upcoming paper by 

M. Arlitt and C. Williamson, entitled ``Web Server Workload Characterization: The Search for Invariants'', to appear in the proceedings of the _1996 ACM SIGMETRICS Conference on the Measurement and Modeling of Computer Systems_ , Philadelphia, PA, May 23-26, 1996. An _<u>extended version</u>_ of this paper is available on-line; see also the _<u>DISCUS home page</u>_ and the group's _<u>publications</u>_ <u>.</u> 

## **Related** 

Permission has been granted to make four of the six data sets discussed in ``Web Server Workload Characterization: The Search for Invariants'' available. The four data sets are: <u>Calgary-HTTP , ClarkNetHTTP , NASA-HTTP , and Saskatchewan-HTTP .</u> 

## **Restrictions** 

The trace may be freely redistributed. 

## **Distribution** 

Available from the Archive in **<u>ASCII format, 5.4 MB gzip compressed</u>** <u>, 52.3 MB uncompressed.</u> 

## Up to <u>Traces In The Internet Traffic Archive.</u> 

