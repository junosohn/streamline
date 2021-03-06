from django.shortcuts import render
from django.shortcuts import redirect
from global_var_and_func import LISTENER_USERID,\
                                sql_update_cmd,\
                                sql_fetchone_cmd,\
                                sql_fetchall_cmd,\
                                sql_delete_cmd

# Create your views here.


def user_info(request, user_id):
    context = {'user_id': user_id}
    return render(request, 'user_info/user_info.html', context)


def display_playlist(request, user_id):
    context = {'user_id': user_id}
    
    # setting it to empty so passing 'context' values won't say variable undefined
    #number_songs_by_artist_result = ''
    
    get_playlist_sql = "SELECT PIS.playlistname, PIS.songname, AID.stagename, A.albumname, CS.tracklength " \
                       "FROM playlistincludessongs PIS " \
                       "JOIN containsong CS ON CS.albumid = PIS.albumid AND CS.songname = PIS.songname " \
                       "JOIN Album A ON A.albumid = CS.albumid " \
                       "JOIN createalbum CA ON CA.albumid = A.albumid " \
                       "JOIN ArtistUserId AID ON AID.userid = CA.userid " \
                       "WHERE PIS.userid = {};".format(user_id)

    # Find total number of songs in the user playlist
    get_song_count = "SELECT COUNT(*) " \
                     "FROM playlistincludessongs PIS " \
                     "JOIN CreatePlaylist CP ON " \
                     "PIS.UserID = CP.UserID AND " \
                     "PIS.PlaylistName = CP.PlaylistName " \
                     "JOIN ListenerUserID LID ON CP.UserID = LID.UserID " \
                     "WHERE PIS.UserID = {}".format(user_id)

    user_playlist = sql_fetchall_cmd(get_playlist_sql)
    
    total_song_count_playlist = sql_fetchone_cmd(get_song_count)
    
    # print(user_playlist)
    # print(total_song_count_playlist)
    context['result'] =  user_playlist
    context['song_count'] = total_song_count_playlist

    # ----- Return user's playlist and number of songs in those playlists by a specific artist (stagename)
    if (request.method == 'POST' and 'stage_name' in request.POST):
        stage_name = request.POST.get('stage_name', None)
        print(stage_name)
        number_songs_by_artist_sql = "SELECT PIS.playlistname, AID.stagename, COUNT(*) \
                                    FROM playlistincludessongs PIS \
                                    JOIN containsong CS ON CS.albumid = PIS.albumid AND CS.songname = PIS.songname \
                                    JOIN havesongs HS ON HS.albumid = CS.albumid AND HS.songname = CS.songname \
                                    JOIN album A ON A.albumid = CS.albumid \
                                    JOIN createalbum CA ON CA.albumid = A.albumid \
                                    JOIN artistuserid AID ON AID.userid = CA.userid \
                                    WHERE PIS.userid = {} AND AID.stagename = \'{}\' \
                                    GROUP BY PIS.playlistname, AID.stagename;".format(user_id,stage_name)
        # returns playlistname, stagename, count
        number_songs_by_artist_result = sql_fetchall_cmd(number_songs_by_artist_sql)
        print (number_songs_by_artist_result)

        
        context[ 'num_songs'] =  number_songs_by_artist_result
        return render(request, 'user_info/playlist.html', context)   


    # -------------------- delete song from playlist  -------------------#

    if request.method == 'POST' and "remove_playlist" in request.POST:
        print("I got here")
        playlist_to_delete = request.POST.get('remove_playlist', None)
        print(playlist_to_delete)
        playlist_to_delete_sql = "DELETE FROM createplaylist " \
                                 "WHERE userid = {} " \
                                 "AND playlistname = \'{}\';".format(user_id,playlist_to_delete)
        sql_delete_cmd(playlist_to_delete_sql)
        print("Executed delete command")
        # redirects back to itself
        return redirect('.')
        # return render(request, 'user_info/playlist.html', context)   
        # -------------------- delete song from playlist END -------------------#

    return render(request, 'user_info/playlist.html', context)

def detail(request, user_id):

    if "select_detail" in request.POST:
        selected_value = request.POST["select_detail"]

        context = {'user_id': user_id,
                   'selected_value': selected_value}

        get_user_sql = "SELECT {} FROM {} " \
                       "WHERE UserId = {};".format(selected_value, LISTENER_USERID, user_id)
        print(get_user_sql)
        result = sql_fetchone_cmd(get_user_sql)
        response = result[0]

        if selected_value == 'email':
            context['email'] = response
        elif selected_value == 'firstname':
            context['firstname'] = response
        elif selected_value == 'lastname':
            context['lastname'] = response
        elif selected_value == 'age':
            context['age'] = response

        return render(request, 'user_info/detail.html', context)

    else:
        selected_value = None

    return render(request, 'user_info/detail.html', {'selected_value': selected_value,'user_id': user_id})


def update_age(request, user_id):
    if request.method == 'POST':
        age = request.POST.get('new_age', None)
        if age != '':
            update_age_sql = "UPDATE {} SET Age={} WHERE UserId={};".format(LISTENER_USERID, age, user_id)
            print(update_age_sql)
            sql_update_cmd(update_age_sql)
            return redirect("/user_info/" + str(user_id) + "/detail/")

    context = {'user_id' : user_id}
    return render(request, 'user_info/update.html', context)


def show_songs(request, user_id):
    if "select_genre" in request.POST:
        selected_value = request.POST["select_genre"]

        get_songs_by_genre_sql = "SELECT CS.SongName, AID.stagename, A.albumname " \
                                 "FROM ContainSong CS " \
                                 "JOIN havesongs HS ON HS.albumid = CS.albumid AND HS.songname = CS.songname " \
                                 "JOIN Album A ON A.albumid = CS.albumid " \
                                 "JOIN createalbum CA ON CA.albumid = A.albumid " \
                                 "JOIN ArtistUserId AID ON AID.userid = CA.userid " \
                                 "WHERE HS.genrename = \'{}\';".format(selected_value)
        print(get_songs_by_genre_sql)
        song_details = sql_fetchall_cmd(get_songs_by_genre_sql)

        context = {'user_id': user_id,
                   'selected_value': selected_value,
                   'result': song_details}
        return render(request, 'user_info/show_songs.html', context)

    else:
        selected_value = None

    return render(request, 'user_info/show_songs.html', {'selected_value': selected_value,'user_id': user_id})


def nested_agg(request, user_id):
    # Return the artist info and the name of their album that has more than 2 songs that are 3 minutes or longer
    nested_agg_sql = "SELECT AN.stagename, AN.firstname, AN.lastname, A.albumname " \
                     "FROM artistname AN " \
                     "JOIN artistuserid AID ON AID.stagename = AN.stagename " \
                     "JOIN createalbum CA ON CA.userid = AID.userid " \
                     "JOIN album A ON A.albumid = CA.albumid " \
                     "WHERE A.albumid IN  " \
                     "( SELECT CS.albumid " \
                     "FROM containsong CS " \
                     "WHERE CS.tracklength >= \'00:03:00\' " \
                     "GROUP BY CS.albumid " \
                     "HAVING COUNT (*) > 2 ); "
    print(nested_agg_sql)
    result= sql_fetchall_cmd(nested_agg_sql)
    context = {'user_id': user_id,
               'result': result}
    return render(request, 'user_info/lucky.html', context)


def show_all_users(request, user_id):

    if "select_users" in request.POST:
        selected_value = request.POST["select_users"]

        get_users_sql = "SELECT {} FROM {} ;".format(selected_value, LISTENER_USERID)

        print(get_users_sql)
        result = sql_fetchall_cmd(get_users_sql)
        context = {'user_id': user_id,
                   'selected_value': selected_value,
                   'result': result}
        return render(request, 'user_info/all_users.html', context)

    else:
        selected_value = None

    return render(request, 'user_info/all_users.html', {'selected_value': selected_value,'user_id': user_id})


def songs_in_all(request, user_id):
    # -------------------- Show songs that appear in all playlists  -------------------#
    # DIVISION QUERY:
    songs_appear_in_all_sql = "SELECT DISTINCT CS.SongName, AID.stagename, A.albumname, CS.tracklength " \
                              "FROM containsong CS " \
                              "JOIN playlistincludessongs PIS ON PIS.songname = CS.songname " \
                              "AND PIS.albumid = CS.albumid " \
                              "JOIN Album A ON A.albumid = CS.albumid " \
                              "JOIN createalbum CA ON CA.albumid = A.albumid " \
                              "JOIN ArtistUserId AID ON AID.userid = CA.userid " \
                              "WHERE " \
                              "NOT EXISTS (" \
                              "(SELECT CP.UserID, CP.playlistname " \
                              "FROM CreatePlaylist CP " \
                              "WHERE CP.playlistname IN ( " \
                              "SELECT playlistname " \
                              "FROM createplaylist " \
                              "WHERE userid = {}) " \
                              ") " \
                              "EXCEPT " \
                              "(SELECT PIS.userid, PIS.playlistname " \
                              "FROM playlistincludessongs PIS, createplaylist CP " \
                              "WHERE PIS.SongName = CS.SongName AND " \
                              "PIS.playlistname = CP.playlistname AND " \
                              "PIS.userid = CP.userid) " \
                              ");".format(user_id)

    songs_appear_in_all = sql_fetchall_cmd(songs_appear_in_all_sql)
    print(songs_appear_in_all)
    context = {'user_id': user_id,
               'songs_appear_in_all': songs_appear_in_all
               }

    return render(request, 'user_info/songs_in_all.html', context)
