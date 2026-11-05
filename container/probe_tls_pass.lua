-- CHR lab-only, TLS transit visibility. No mutation or injection.
function zapret2_tls_pass(ctx, desync)
    if desync.dis and desync.dis.tcp and desync.dis.payload
       and #desync.dis.payload > 0 then
        DLOG("ZAPRET2_FORWARDED_TLS_LUA_PASS payload_len=" .. tostring(#desync.dis.payload))
    end
    return VERDICT_PASS
end
