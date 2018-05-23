#!/bin/bash

echo "Upload dashboards with related components..."
curl -s -k -XPOST $KIBANA_URL/api/kibana/dashboards/import -u "$KIBANA_USER:$KIBANA_PASSWORD" -H 'Content-Type: application/json' -H 'kbn-xsrf:true' -d @dashboard_eventdata_traffic.json
echo ""
curl -s -k -XPOST $KIBANA_URL/api/kibana/dashboards/import -u "$KIBANA_USER:$KIBANA_PASSWORD" -H 'Content-Type: application/json' -H 'kbn-xsrf:true' -d @dashboard_eventdata_content_analysis.json
echo ""