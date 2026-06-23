import urllib.request, time, sys
time.sleep(2)
try:
    r = urllib.request.urlopen('http://localhost:8080')
    html = r.read().decode()
    print('HTTP', r.status)
    print('weight=3 seeded :', 'weight": 3' in html)
    print('invalid addr gone:', 'gfdseasrdtfyguhij' not in html)
except Exception as e:
    print('ERROR:', e)
    sys.exit(1)
