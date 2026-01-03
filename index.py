if answer:
                        status.update(label=f"OBJ COMPLETE via {eng.upper()} PROTOCOL", state="complete", expanded=False)
                        _render_chat_message("assistant", answer, str(uuid.uuid4()))
                        st.session_state.user_chats[st.session_state.current_chat_id]["messages"].append({
                            "id": str(uuid.uuid4()),
                            "role": "assistant",
                            "content": answer
                        })
                        st.session_state.user_chats[st.session_state.current_chat_id]["last_updated"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        _sync_user_chats_to_vault()
                        _log_user_action(f"AI response generated for chat '{st.session_state.current_chat_id}'.")
                        st.rerun()
                    else:
                        status.update(label="☠️ MISSION ABORTED. NO AI RESPONSE GENERATED.", state="error", expanded=True)
                        error_message = "☠️ MISSION ABORTED. NO AI RESPONSE GENERATED. SYSTEM MALFUNCTION OR API EXHAUSTION. VERIFY CONFIGURATION AND RETRY."
                        _render_chat_message("assistant", error_message, str(uuid.uuid4()))
                        st.session_state.user_chats[st.session_state.current_chat_id]["messages"].append({
                            "id": str(uuid.uuid4()),
                            "role": "assistant",
                            "content": error_message
                        })
                        st.session_state.user_chats[st.session_state.current_chat_id]["last_updated"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        _sync_user_chats_to_vault()
                        _log_user_action(f"AI response failed for chat '{st.session_state.current_chat_id}'.")
                        st.rerun()

# --- Entry Point ---
if name == "main":
    main()
