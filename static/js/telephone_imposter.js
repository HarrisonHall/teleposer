// Client Side Javascript to receive numbers.
var socket;
var WAITING = 0, PLAYING = 1, VOTING = 2, OVER = 3;

// Show elements based on bool
function show_id(id, show) {
	let element = $("#"+id);
	if (show) {
		element.show();
	} else {
		element.hide();
	}
}

// Game logic to show elements
function collapse_necessary() {
	show_id("players_wrapper", true);
	show_id(
		"ti_settings_wrapper",
		(game_data.leader == username) &&
			(game_data.state == WAITING)
	);
	show_id(
		"write_sentence_wrapper",
		(game_data.state == PLAYING) &&
			(!game_data.mixups.hasOwnProperty(username))
	);
	show_id(
		"edit_sentence_wrapper",
		(game_data.state == PLAYING) &&
			(user_submitting_for != "")
	);
	show_id(
		"vote_player_wrapper",
		(game_data.state == VOTING) &&
			(!voted_yet)
	);
	show_id("identity_wrapper", [PLAYING, VOTING].includes(game_data.state));
	show_id("endgame_wrapper", game_data.state == OVER);
}

function update_identity() {
	if (username == game_data.imposter) {
		$("#identity_text").text("You are the imposter.");
		$("#identity_text_sub").text("Try to mess the prompts up without getting caught.");
	} else {
		$("#identity_text").text("You are a normal player.");
		$("#identity_text_sub").text("Try to figure out what your friends meant.");
	}
}

function update_players() {
	let players_t = "";
	for (let i=0; i < game_data.players.length; i++) {
		players_t += game_data.players[i] + ", ";
	}
	$("#players_text").text(players_t)
}

function update_write_sentence() {
	let phrase = "Your sentence must be " + game_data.settings.words.toString() + " words long.";
	$("#write_sentence_text").text(phrase);
}

function update_edit_sentence() {
	// Check what sentence to edit
	let edit_sentence = false;
	if (user_submitting_for != "") edit_sentence = true;
	
	let sent_first_sentence = false;
	if (game_data.phrases.hasOwnProperty(username)) {
		sent_first_sentence = (game_data.phrases[username].length > 0);
		edit_sentence = false
	}
	
	if (!edit_sentence && sent_first_sentence) {
		let j = 0;
		for (let i = game_data.players.indexOf(username); i < game_data.players.length + game_data.players.indexOf(username); i++) {
			player = game_data.players[i % game_data.players.length];
			if (!game_data.phrases.hasOwnProperty(player)) continue;
			if (game_data.phrases[player].length == j) {
				edit_sentence = true;
				user_submitting_for = player;
				break;
			}
			j++;
		}
	}
	if (edit_sentence)
		$("#edit_sentence_text").text("Edit this sentence: "+game_data.mixups[user_submitting_for])
}

function update_vote_area() {
	if (game_data.state != VOTING) return;
	if (voted_yet) return;
	if (made_vote_form) return;
	console.log("Making update vote area");
	$("#vote_area").append("<thead><tr>");
	$("#vote_area").append('<th scope="col"></th>');
	for (let i=0; i < game_data.players.length; i++)
		$("#vote_area").append('<th scope="col">'+game_data.players[i]+'</th>');
	$("#vote_area").append('<th scope="col"></th>');
	$("#vote_area").append("</tr></thead>");
	$("#vote_area").append("<tbody>");
	for (let i=0; i<game_data.players.length; i++) {
		$("#vote_area").append("<tbody>");
		$("#vote_area").append("<tr>");
		$("#vote_area").append('<th scope="row">'+game_data.players[i]+'</th>');
		for (let j=0; j<game_data.players.length; j++) {
			$("#vote_area").append("<td>"+game_data.phrases[game_data.players[j]][i]+"</td>");
		}
		$("#vote_area").append(
			'<td><button type="button" class="btn btn-primary" onclick="submit_vote(\'' +
				game_data.players[i] + '\')">' + game_data.players[i] + '</button></td>'
		);
		$("#vote_area").append("<tbody>");
	    $("#vote_area").append("</tr>");
	}
	$("#vote_area").append("</tbody>");
	made_vote_form = true;
}

function update_endgame() {
	message = "";
	for (let i=0; i < game_data.winners.length; i++)
		message += game_data.winners[i]+", ";
	message += "won."
	$("#endgame_text").text(message);
}

function objectifyForm(formArray) {
    let returnjson = {};
    for (let i = 0; i < formArray.length; i++){
        returnjson[formArray[i]['name']] = formArray[i]['value'];
    }
    return returnjson;
}

function submit_settings(event) {
	event.preventDefault();
	let form = $("#settings_form");
	let formjson = objectifyForm(form.serializeArray());
	socket.emit(
		"ti_update_settings",
		formjson
	);
}

function submit_first_sentence(event) {
	event.preventDefault();
	let form = $("#write_sentence_form");
	let formjson = objectifyForm(form.serializeArray());
	formjson["user"] = username;
	user_submitting_for = "";
	socket.emit(
		"ti_submit_sentence",
		formjson
	);
}

function submit_sentence(event) {
	event.preventDefault();
	let form = $("#edit_sentence_form");
	let formjson = objectifyForm(form.serializeArray());
	formjson["user"] = user_submitting_for;
	user_submitting_for = "";
	socket.emit(
		"ti_submit_sentence",
		formjson
	);
}

function submit_vote(user) {
	voted_yet = true;
	socket.emit(
		"ti_vote",
		{
			"user": username,
			"vote": user
		}
	);
}


// When document has loaded
$(document).ready( function() {
    //socket = io();
	socket = io.connect('https://' + document.domain + ':' + location.port);
    socket.on('connect', function() {
        socket.emit('ti_connected', {});
    });
	socket.on('ti_update', function(arg) {
		console.log(arg);
		game_data = arg;
		if (!username_set) {
			username_set = true;
			username = game_data.username;
		}
		update_identity();
		update_players();
		update_write_sentence();
		update_edit_sentence();
		update_vote_area();
		update_endgame()
		collapse_necessary();
		if (game_data.state == OVER) socket.disconnect();
	});
	$("#settings_form").submit(submit_settings); // alter settings change
	$("#write_sentence_form").submit(submit_first_sentence);
	$("#edit_sentence_form").submit(submit_sentence);
});
