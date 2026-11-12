---
# --- bibliographic record ---
entry_type: misc
title: "ClarkNet-HTTP trace"
authors:
  - "Internet Traffic Archive"
year: 1995
venue: "Internet Traffic Archive, Lawrence Berkeley National Laboratory"
volume: ""
issue: ""
pages: ""
publisher: ""
doi: ""
arxiv: ""
url: "https://ita.ee.lbl.gov/html/contrib/ClarkNet-HTTP.html"

# --- archive record ---
source_pdf: clarknet-http-trace-ita-1995.pdf
source_sha256: ed39283a166571a4e5792d8f0faa26c61a7292723147c55a304e83bc1fe9e5ef
pdf_pages: 1
converted: 2026-11-12
record_source: manual
review: "web page printed to PDF on 2026-11-12; trace contributed by Martin Arlitt and Carey Williamson"
key_insight: "Two 7-day logs, 28 August to 10 September 1995, 3,328,587 requests to the ClarkNet web server. Collected by Stephen Balbach, contributed by Martin Arlitt and Carey Williamson."
first_page: "ClarkNet-HTTP Description These two traces contain two week's worth of all HTTP requests to the ClarkNet WWW server. ClarkNet is a full Internet access provider for the Metro Baltimore-Washington DC a"
---
# **_ClarkNet-HTTP_** 

## **Description** 

These two traces contain two week's worth of all HTTP requests to the ClarkNet WWW server. ClarkNet is a full Internet access provider for the Metro Baltimore-Washington DC area. 

## **Format** 

The logs are an ASCII file with one line per request, with the following columns: 

1. **host** making the request. A hostname when possible, otherwise the Internet address if the name could not be looked up. 

2. **timestamp** in the format "DAY MON DD HH:MM:SS YYYY", where **DAY** is the day of the week, **MON** is the name of the month, **DD** is the day of the month, **HH:MM:SS** is the time of day using a 24-hour clock, and **YYYY** is the year. The timezone is -0400. 

3. **request** given in quotes. 

4. **HTTP reply code** . 

5. **bytes in the reply** . 

## **Measurement** 

The first log was collected from 00:00:00 August 28, 1995 through 23:59:59 September 3, 1995, a total of 7 days. The second log was collected from 00:00:00 September 4, 1995 through 23:59:59 September 10, 1995, a total of 7 days. In this two week period there were 3,328,587 requests. Timestamps have 1 second resolution. 

## **Privacy** 

The logs fully preserve the originating host and HTTP request. Please do not however attempt any analysis beyond general traffic patterns. 

## **Acknowledgements** 

The logs was collected by Stephen Balbach of ClarkNet, and contributed by Martin Arlitt ( _mfa126@cs.usask.ca_ ) and Carey Williamson ( _carey@cs.usask.ca_ ) of the University of Saskatchewan. 

## **Publications** 

This is one of six data sets analyzed in an upcoming paper by 

M. Arlitt and C. Williamson, entitled ``Web Server Workload Characterization: The Search for Invariants'', to appear in the proceedings of the _1996 ACM SIGMETRICS Conference on the Measurement and Modeling of Computer Systems_ , Philadelphia, PA, May 23-26, 1996. An _<u>extended version</u>_ of this paper is available on-line; see also the _<u>DISCUS home page</u>_ and the group's _<u>publications</u>_ <u>.</u> 

## **Related** 

Permission has been granted to make four of the six data sets discussed in ``Web Server Workload Characterization: The Search for Invariants'' available. The four data sets are: <u>Calgary-HTTP , ClarkNetHTTP , NASA-HTTP , and Saskatchewan-HTTP .</u> 

## **Restrictions** 

The traces may be freely redistributed. 

## **Distribution** 

Available from the Archive in **<u>Aug 24 to Sep 03, ASCII format, 21.8 MB gzip compressed</u>** <u>, 171.0 MB</u> uncompressed, and **<u>Sep 04 to Sep 10, ASCII format, 20.8 MB gzip compressed</u>** <u>, 172.5 MB</u> uncompressed. 

## Up to <u>Traces In The Internet Traffic Archive.</u> 

