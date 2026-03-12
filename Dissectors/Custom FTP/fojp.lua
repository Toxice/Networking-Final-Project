-- Define the Protocol
local fojp_proto = Proto("FOJP", "File Transfer Over JSON")

-- Field Definitions
local f_type        = ProtoField.string("fojp.type", "Message Type")
local f_files       = ProtoField.string("fojp.files", "Available Files")
local f_filename    = ProtoField.string("fojp.filename", "Requested File")
local f_mode        = ProtoField.string("fojp.mode", "Transfer Mode")
local f_status      = ProtoField.string("fojp.status", "Status")
local f_data_port   = ProtoField.uint16("fojp.data_port", "Dynamic Data Port")
local f_ack_num     = ProtoField.int32("fojp.ack_num", "RUDP ACK Number")

fojp_proto.fields = { f_type, f_files, f_filename, f_mode, f_status, f_data_port, f_ack_num }

-- Helper to extract JSON values
local function get_json_val(str, key)
    local pattern = '"' .. key .. '"%s*:%s*"?([^",%s%}]*)"?'
    return str:match(pattern)
end

function fojp_proto.dissector(buffer, pinfo, tree)
    local length = buffer:len()
    if length == 0 then return end

    local raw_data = buffer(0, length):string()

    if not (raw_data:match("^%s*{") or raw_data:match("}$")) then return end

    pinfo.cols.protocol = "FOJP"
    local subtree = tree:add(fojp_proto, buffer(), "FOJP Control Protocol")

    local m_type = get_json_val(raw_data, "type")
    local status = get_json_val(raw_data, "status")
    local d_port = get_json_val(raw_data, "data_port")
    local fname  = get_json_val(raw_data, "filename")
    local mode   = get_json_val(raw_data, "mode")

    -- --- Logic for Control Channel ---

    if m_type == "MENU" then
        subtree:add(f_type, "MENU")
        -- Optimized File List Extraction
        local files = raw_data:match('"files"%s*:%s*%[([^%]]*)%]')
        if files then
            local cleaned_files = files:gsub('"', ''):gsub('%s+', '')
            -- Pass cleaned_files as the third argument to display it in the tree label
            subtree:add(f_files, buffer(), cleaned_files)
        end
        pinfo.cols.info = "Sending File Menu"

    elseif fname then
        subtree:add(f_filename, buffer(), fname)
        if mode then subtree:add(f_mode, buffer(), mode) end
        pinfo.cols.info = "Request [" .. fname .. "] via " .. (mode or "UNKNOWN")

    elseif status then
        subtree:add(f_status, buffer(), status)
        if d_port then
            subtree:add(f_data_port, buffer(), tonumber(d_port))
            pinfo.cols.info = "READY on Port " .. d_port
        else
            pinfo.cols.info = "Status -> " .. status
        end

    elseif m_type == "ACK" then
        local ack = get_json_val(raw_data, "num")
        subtree:add(f_type, "RUDP_ACK")
        if ack then
            subtree:add(f_ack_num, buffer(), tonumber(ack))
            pinfo.cols.info = "RUDP: ACK #" .. ack
        end
    end
end

local tcp_port = DissectorTable.get("tcp.port")
tcp_port:add(2121, fojp_proto)