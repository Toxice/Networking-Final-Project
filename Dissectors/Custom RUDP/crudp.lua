-- CRUDP Protocol Dissector (Binary Version)
local crudp_proto = Proto("CRUDP", "Custom Reliable UDP")

-- Header Fields
local f_seq_num = ProtoField.uint32("crudp.seq_num", "Sequence Number", base.DEC)
local f_total_p = ProtoField.uint32("crudp.total_packets", "Total Packets", base.DEC)
local f_flags   = ProtoField.uint8("crudp.flags", "Flags", base.HEX)

-- Bitmask Flags
local f_flag_syn = ProtoField.bool("crudp.flags.syn", "SYN (Connection Init)", 8, nil, 0x04)
local f_flag_ack = ProtoField.bool("crudp.flags.ack", "ACK (Acknowledgment)", 8, nil, 0x02)
local f_flag_fin = ProtoField.bool("crudp.flags.fin", "FIN (Teardown)", 8, nil, 0x01)

-- Padding and Meta
local f_reserved = ProtoField.bytes("crudp.reserved", "Padding (3 bytes)", base.NONE)
local f_pkt_size = ProtoField.uint32("crudp.size", "Total Frame Size", base.DEC)

crudp_proto.fields = { f_seq_num, f_total_p, f_flags, f_flag_syn, f_flag_ack, f_flag_fin, f_reserved, f_pkt_size }

function crudp_proto.dissector(buffer, pinfo, tree)
    local length = buffer:len()
    if length < 12 then return end

    pinfo.cols.protocol = "CRUDP"

    local seq_num = buffer(0, 4):uint()
    local total_p = buffer(4, 4):uint()
    local flags   = buffer(8, 1):uint()

    -- Determine Packet Type
    local p_type = "DATA"
    if bit.band(flags, 0x04) ~= 0 then p_type = "SYN"
    elseif bit.band(flags, 0x02) ~= 0 then p_type = "ACK"
    elseif bit.band(flags, 0x01) ~= 0 then p_type = "FIN"
    end

    -- Update Info Column
    if p_type == "DATA" then
        pinfo.cols.info = string.format("DATA | Seq: %d | Total: %d", seq_num, total_p)
    else
        pinfo.cols.info = string.format("%s | Num: %d", p_type, seq_num)
    end

    -- Main Header Tree
    local subtree = tree:add(crudp_proto, buffer(0, 12), "CRUDP Header (" .. p_type .. ")")
    subtree:add(f_seq_num, buffer(0, 4))
    subtree:add(f_total_p, buffer(4, 4))

    -- Flags Subtree
    local flag_tree = subtree:add(f_flags, buffer(8, 1))

    -- Logical Data Display
    if flags == 0 then
        flag_tree:add(buffer(8,1), ".... ...0 = Data: True"):set_generated()
    else
        flag_tree:add(buffer(8,1), ".... ...0 = Data: False"):set_generated()
    end

    flag_tree:add(f_flag_syn, buffer(8, 1))
    flag_tree:add(f_flag_ack, buffer(8, 1))
    flag_tree:add(f_flag_fin, buffer(8, 1))

    -- Padding and Size
    subtree:add(f_reserved, buffer(9, 3))
    subtree:add(f_pkt_size, length):set_generated()

    -- Payload Section
    if length > 12 then
        local payload_len = length - 12
        tree:add(buffer(12, payload_len), "Payload Data (" .. payload_len .. " bytes)")
    end
end

local udp_port = DissectorTable.get("udp.port")
udp_port:add(56185, crudp_proto)