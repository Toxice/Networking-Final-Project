local dns_json_proto = Proto("dns_json", "JSON DNS Protocol")

-- Standalone Fields definition
local f_url     = ProtoField.string("dns_json.url", "Queried URL")
local f_resp_ip = ProtoField.string("dns_json.resolved_ip", "Resolved IP")

-- Registering standalone fields only
dns_json_proto.fields = { f_url, f_resp_ip }

function dns_json_proto.dissector(buffer, pinfo, tree)
    pinfo.cols.protocol = "JSON_DNS"
    local raw_data = buffer():string()

    -- Create the main tree item
    local subtree = tree:add(dns_json_proto, buffer(), "JSON DNS Data")

    -- 1. Extract values via pattern matching
    local url = string.match(raw_data, '"url"%s*:%s*"(.-)"')
    local ip  = string.match(raw_data, '"ip"%s*:%s*"(.-)"')

    -- 2. Add fields to tree ONLY if they exist in the JSON
    if url then
        subtree:add(f_url, url)
        pinfo.cols.info = "DNS Query: " .. url
    end

    if ip then
        subtree:add(f_resp_ip, ip)
        pinfo.cols.info = "DNS Response: " .. ip
    end

    -- 3. Raw JSON is no longer added to the tree
end

local udp_port = DissectorTable.get("udp.port")
udp_port:add(9000, dns_json_proto)
-- If you're testing on mDNS port, uncomment the line below:
-- udp_port:add(5353, dns_json_proto)