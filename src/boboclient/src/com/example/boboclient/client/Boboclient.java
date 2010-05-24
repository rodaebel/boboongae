package com.example.boboclient.client;

import com.google.gwt.core.client.EntryPoint;
import com.google.gwt.core.client.JavaScriptObject;
import com.google.gwt.core.client.JsArray;
import com.google.gwt.http.client.URL;


/**
 * Entry point class.
 */
public class Boboclient implements EntryPoint {

	/**
	 * The JSON URI.
	 */
	private static final String JSON_URI = "/json";

	/**
	 * JSON.
	 */
	private final native JsArray<BoboData> asArrayOfBboboData(JavaScriptObject jso) /*-{
		return jso;
	}-*/;

	private int jsonRequestId = 0;

	/** Make call to remote server.
	 *
	 * This JSNI method creates a dynamically-loaded <script> element as a work
	 * around for the Same-Origin Policy restrictions.
	 *
	 *   http://www.w3.org/Security/wiki/Same_Origin_Policy
	 *
	 * The src attribute is the URL of the JSON data with the name of a
	 * callback function appended. When the script executes, it fetches the
	 * padded JSON; the JSON data is passed as an argument of the callback
	 * function. When the callback function executes, it calls the Java
	 * handleJsonResponse method and passes it the JSON data as a JavaScript
	 * object.
	 *
	 * This implementation generates callback function names sequentially in
	 * case of multiple pending requests.
	 */
	public native static void getJson(int requestId, String url, Boboclient handler) /*-{
		var callback = "callback" + requestId;

		// [1] Create a script element.
		var script = document.createElement("script");
		script.setAttribute("src", url+callback);
		script.setAttribute("type", "text/javascript");

		// [2] Define the callback function on the window object.
		window[callback] = function(jsonObj) {

		// [3]
			handler.@com.example.boboclient.client.Boboclient::handleJsonResponse(Lcom/google/gwt/core/client/JavaScriptObject;)(jsonObj);
			window[callback + "done"] = true;
		}

		// [4] JSON download has 1-second timeout.
		setTimeout(function() {
			if (!window[callback + "done"]) {
				handler.@com.example.boboclient.client.Boboclient::handleJsonResponse(Lcom/google/gwt/core/client/JavaScriptObject;)(null);
			}

			// [5] Cleanup. Remove script and callback elements.
			document.body.removeChild(script);
			delete window[callback];
			delete window[callback + "done"];
		}, 1000);

		// [6] Attach the script element to the document body.
		document.body.appendChild(script);
	}-*/;

	/**
	 * Returns the Service URL.
	 */
	public final native static String getServiceURL() /*-{
		return $wnd.SERVICE_URL;
	}-*/;

	/**
	 * Display message.
	 * @param msg
	 */
	private native static void displayMessage(String msg) /*-{
		$wnd.alert(msg);
	}-*/;

	/**
	 * Handle the response to the request for our data from the remote server.
	 */
	public void handleJsonResponse(JavaScriptObject jso) {
		if (jso == null) {
			displayMessage("No JSON data available.");
			return;
		}
	}

	private void refreshData() {
		String url = getServiceURL() + JSON_URI;

		// Append the name of the callback function to the JSON URL.
		url = URL.encode(url) + "?callback=";

		// Send request to server by replacing RequestBuilder code with a
		// call to a JSNI method.
		getJson(jsonRequestId++, url, this);
	}

	public void onModuleLoad() {
		refreshData();
	}
}
