-- Define the Protocol
local fojp_proto = Proto("FOJP", "File Transfer Over JSON")

-- Field Definitions for Wireshark Filtering
local f_type        = ProtoField.string("fojp.type", "Message Type")
local f_files       = ProtoField.string("fojp.files", "Available Files")
local f_filename    = ProtoField.string("fojp.filename", "Requested File")
local f_mode        = ProtoField.string("fojp.mode", "Transfer Mode")
local f_status      = ProtoField.string("fojp.status", "Status")
local f_data_port   = ProtoField.uint16("fojp.data_port", "Dynamic Data Port")
local f_ack_num     = ProtoField.int32("fojp.ack_num", "RUDP ACK Number")

fojp_proto.fields = { f_type, f_files, f_filename, f_mode, f_status, f_data_port, f_ack_num }

-- Helper to extract JSON values more robustly
local function get_json_val(str, key)
    -- Matches "key": "value" or "key": value
    local pattern = '"' .. key .. '"%s*:%s*"?([^",%s%}]*)"?'
    return str:match(pattern)
end

function fojp_proto.dissector(buffer, pinfo, tree)
    local length = buffer:len()
    if length == 0 then return end

    local raw_data = buffer(0, length):string()
    
    -- Basic JSON validation
    if not (raw_data:match("^%s*{") or raw_data:match("}$")) then return end

    pinfo.cols.protocol = "FOJP"
    local subtree = tree:add(fojp_proto, buffer(), "FOJP Control Protocol")

    -- 1. Parse Message Type (Menu, ACK, etc.)
    local m_type = get_json_val(raw_data, "type")
    
    -- 2. Parse Server Response (Status & Data Port)
    local status = get_json_val(raw_data, "status")
    local d_port = get_json_val(raw_data, "data_port")

    -- 3. Parse Client Request (Filename & Mode)
    local fname  = get_json_val(raw_data, "filename")
    local mode   = get_json_val(raw_data, "mode")

    -- --- Logic for Control Channel (TCP 2121) ---
    
    -- Server Sending Menu
    if m_type == "MENU" then
        subtree:add(f_type, buffer(), "MENU")
        local files = raw_data:match('"files"%s*:%s*%[([^%]]*)%]')
        if files then subtree:add(f_files, buffer(), files:gsub('"', '')) end
        pinfo.cols.info = "Sending File Menu"

    -- Client Requesting File
    elseif fname then
        subtree:add(f_filename, buffer(), fname)
        if mode then subtree:add(f_mode, buffer(), mode) end
        pinfo.cols.info = "Request [" .. fname .. "] via " .. (mode or "UNKNOWN")

    -- Server Ready Response
    elseif status then
        subtree:add(f_status, buffer(), status)
        if d_port then 
            subtree:add(f_data_port, buffer(), tonumber(d_port))
            pinfo.cols.info = "READY on Port " .. d_port
        else
            pinfo.cols.info = "Status -> " .. status
        end

    -- RUDP Feedback (on UDP ports)
    elseif m_type == "ACK" then
        local ack = get_json_val(raw_data, "num")
        subtree:add(f_type, buffer(), "RUDP_ACK")
        if ack then 
            subtree:add(f_ack_num, buffer(), tonumber(ack))
            pinfo.cols.info = "RUDP: ACK #" .. ack
        end
    end

    -- Always call the built-in JSON dissector for the full tree view
   -- Dissector.get("json"):call(buffer, pinfo, tree)
end

-- Register to the control port
local tcp_port = DissectorTable.get("tcp.port")
tcp_port:add(2121, fojp_proto)