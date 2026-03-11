-- CRUDP Protocol Dissector (Optimized)
local crudp_proto = Proto("CRUDP", "Custom Reliable UDP")

-- Header Fields Definitions
local f_seq_num = ProtoField.uint32("crudp.seq_num", "Packet Number", base.DEC)
local f_total_p = ProtoField.uint32("crudp.total_packets", "Total Packets", base.DEC)
local f_ack_num  = ProtoField.int32("crudp.ack_num", "ACK Number", base.DEC)
local f_pkt_size = ProtoField.uint32("crudp.size", "Packet Size", base.DEC)
local f_win_size = ProtoField.uint32("crudp.window", "Window Size", base.DEC)

crudp_proto.fields = { f_seq_num, f_total_p, f_ack_num, f_pkt_size, f_win_size }

function crudp_proto.dissector(buffer, pinfo, tree)
    local length = buffer:len()
    if length == 0 then return end

    pinfo.cols.protocol = "CRUDP"
    
    -- 1. Handle "DONE" Signal
    if length == 4 and buffer(0, 4):raw() == "DONE" then
        pinfo.cols.info = "FINALIZE"
        tree:add(crudp_proto, buffer(0, 4), "CRUDP Protocol: FINALIZE")
        return
    end

    -- 2. Handle ACKs (JSON)
    local first_byte = buffer(0, 1):uint()
    if first_byte == 123 then -- ASCII '{'
        local json_str = buffer(0, length):string()
        local ack_num = json_str:match("\"num\"%s*:%s*(-?%d+)")

        if ack_num then
            pinfo.cols.info = string.format("ACK | Win: 10 | Size: %d | Num: %s", length, ack_num)
            -- Use the whole buffer for ACKs since the whole thing is the JSON message
            local subtree = tree:add(crudp_proto, buffer(), "CRUDP Protocol Metrics (ACK)")
            subtree:add(f_ack_num, tonumber(ack_num))
            subtree:add(f_win_size, 10):set_generated()
            subtree:add(f_pkt_size, length):set_generated()
        end
        return
    end

    -- 3. Handle Data Packets
    if length >= 8 then
        local seq_num = buffer(0, 4):uint()
        local total_packets = buffer(4, 4):uint()

        pinfo.cols.info = string.format("DATA | Win: 10 | Size: %d | Num: %d", length, seq_num)

        -- PERFORMANCE FIX: Only add the first 8 bytes (Header) to the tree
        -- This prevents the "gibberish" payload from being highlighted/associated with your tree
        local subtree = tree:add(crudp_proto, buffer(0, 8), "CRUDP Header (Payload Hidden)")

        subtree:add(f_seq_num, buffer(0, 4))
        subtree:add(f_total_p, buffer(4, 4)) -- Added this since it's in your Python header!
        subtree:add(f_win_size, 10):set_generated()
        subtree:add(f_pkt_size, length):set_generated()
    end
end

local udp_port = DissectorTable.get("udp.port")
udp_port:add(56185, crudp_proto)