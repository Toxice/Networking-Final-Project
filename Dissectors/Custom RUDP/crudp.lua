-- CRUDP Protocol Dissector (Custom RUDP)
local crudp_proto = Proto("CRUDP", "Custom Reliable UDP")

-- Header Fields Definitions
local f_seq_num = ProtoField.uint32("crudp.seq_num", "Sequence Number", base.DEC)
local f_total_p = ProtoField.uint32("crudp.total_packets", "Total Packets", base.DEC)
local f_payload = ProtoField.bytes("crudp.payload", "Payload Data")

-- Parsed ACK Fields
local f_ack_type = ProtoField.string("crudp.ack_type", "ACK Type")
local f_ack_num  = ProtoField.int32("crudp.ack_num", "ACK Number")

crudp_proto.fields = { f_seq_num, f_total_p, f_payload, f_ack_type, f_ack_num }

function crudp_proto.dissector(buffer, pinfo, tree)
    local length = buffer:len()
    if length == 0 then return end

    pinfo.cols.protocol = "CRUDP"
    local subtree = tree:add(crudp_proto, buffer(), "Custom RUDP (CRUDP) Data")

    -- 1. Check for "DONE" signal
    if length == 4 and buffer(0, 4):raw() == "DONE" then
        pinfo.cols.info = "FINALIZE (DONE)"
        subtree:add(buffer(0, 4), "Status: DONE")
        return
    end

    -- 2. Check if it's an ACK (JSON format starting with '{')
    local first_byte = buffer(0, 1):uint()
    if first_byte == 123 then -- ASCII for '{'
        local json_str = buffer(0, length):string()
        
        -- Basic Pattern Matching to parse JSON fields manually
        local ack_type = json_str:match("\"type\"%s*:%s*\"(%w+)\"")
        local ack_num = json_str:match("\"num\"%s*:%s*(-?%d+)")

        if ack_type and ack_num then
            pinfo.cols.info = string.format("ACK: %s (Num: %s)", ack_type, ack_num)
            subtree:add(f_ack_type, ack_type):set_generated()
            subtree:add(f_ack_num, tonumber(ack_num)):set_generated()
            subtree:add(buffer(0, length), "Raw JSON: " .. json_str)
        else
            pinfo.cols.info = "Malformed ACK JSON"
        end
        return
    end

    -- 3. Binary Data Packet (Header is 8 bytes: !II)
    if length >= 8 then
        -- Matches your Python struct.pack("!II", ...)
        local seq_num = buffer(0, 4):uint()
        local total_packets = buffer(4, 4):uint()
        
        pinfo.cols.info = string.format("Data: Seq %d / Total %d", seq_num, total_packets)
        
        subtree:add(f_seq_num, buffer(0, 4))
        subtree:add(f_total_p, buffer(4, 4))
        
        if length > 8 then
            subtree:add(f_payload, buffer(8))
        end
    end
end

-- Register to your specific port (e.g., 56185 from your screenshot)
local udp_port = DissectorTable.get("udp.port")
udp_port:add(56185, crudp_proto)