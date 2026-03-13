local dhcp_json_proto = Proto("dhcp_json", "JSON DHCP Protocol")

-- Standalone Fields definition
local f_msg_type = ProtoField.string("dhcp_json.type", "Message Type")
local f_xid      = ProtoField.string("dhcp_json.xid", "Transaction ID")
local f_ip       = ProtoField.string("dhcp_json.ip", "Assigned IP Address")
local f_dns      = ProtoField.string("dhcp_json.dns", "DNS Server IP")

-- Registering fields (Removed f_payload here)
dhcp_json_proto.fields = { f_msg_type, f_xid, f_ip, f_dns }

function dhcp_json_proto.dissector(buffer, pinfo, tree)
    pinfo.cols.protocol = "JSON_DHCP"

    -- Convert buffer to string for pattern matching
    local raw_data = buffer():string()

    -- Create the main tree item
    local subtree = tree:add(dhcp_json_proto, buffer(), "JSON DHCP Protocol Data")

    -- 1. Extract values using pattern matching
    local msg_type = string.match(raw_data, '"message_type"%s*:%s*"(.-)"')
    local xid      = string.match(raw_data, '"transaction_id"%s*:%s*([^%s,}]+)')
    local ip       = string.match(raw_data, '"ip_address"%s*:%s*"(.-)"') or string.match(raw_data, '"requested_ip"%s*:%s*"(.-)"')
    local dns      = string.match(raw_data, '"dns_server"%s*:%s*"(.-)"')

    -- 2. Add fields to tree as Standalones (No raw JSON blob)
    if msg_type then
        subtree:add(f_msg_type, msg_type)
    end

    if xid then
        subtree:add(f_xid, xid)
    end

    if ip then
        subtree:add(f_ip, ip)
    end

    if dns then
        subtree:add(f_dns, dns)
    end

    -- 3. Update the Wireshark Info Column for quick scanning
    pinfo.cols.info = "DHCP " .. (msg_type or "Unknown") .. " [ID: " .. (xid or "?") .. "]"
end

-- Map to your custom ports
local udp_port = DissectorTable.get("udp.port")
udp_port:add(6767, dhcp_json_proto)
udp_port:add(6868, dhcp_json_proto)