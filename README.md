ExMerge.py is PST extractor tool for the Microsoft ExMerge utility. Greatly simplifies automated extrating PST's from Exchange servers for migration or backup purposes. Althouth, it is constrained to 2GB PST files due to ExMerge.exe limitation, this tool will automatically fine tune the extractions to ensure that this size limit is not a hard failure.

    # Extract all emails for users defined in configuration file for date range 01/2000 thru 02/2001 in 3 month blocks and encrypt with foobar
    % python .\ExMerge.py -y 2000 -m 1 -Y 2001 -M 2 -i 3 -e foobar


# Features
- Optional encryption of PST
- Automatic renaming and organization of PSTs on export
- Self healing extraction logic that prevents hitting 2GB limit
- Organizes PSTs by Folder and prepends Dates for easy sorting
- verbose logs stored with PST for debugging

# Current Status
Was developed for a Production migration out of Exchange 2003. Used only once but spent a bit of extra time polishing the code. This tool comes without warranty.


# Installation
- Download and deploy ExMerge.exe from Microsoft
  - Deploy ExMerge.exe to Exchange server installation directory
- Ensure you have full read rights to all Exchange accounts to be extracted
- Install Python 2.7
- Install 7zip (if using encryption option)
- Choose output directory for extracts
  - If space is not available locally, this can be a mapped network drive
- Create a temporary directory for working files
  - This should be on the same server running this script
- put configurations in `prefs.json`
- Add users to be processed in `users_in.txt`
  - Line separated list of LDAP User ID's





# prefs.json
All entries below are required

<table>
<tr>
<th>Field</th>
<th>Description</th>
</tr><tr>
<td>exch_server</td>
<td>Exchange Server Name</td>
</tr><tr>
<td>dir_output</td>
<td>Base directory to output PST extracts</td>
</tr><tr>
<td>temp_dir</td>
<td>Temp directory on local server to put working filesy</td>
</tr><tr>
<td>file_exm_exe</td>
<td>Full path to ExMerge.exe</td>
</tr><tr>
<td>ldap_base</td>
<td>LDAP Base DN ending with CN=. Exclude user ID
<br> eg: /O=MYCO/OU=FIRST ADMINISTRATIVE GROUP/CN=RECIPIENTS/CN=
<br> LDAP User ID will be auto appended to this string</td>
</tr>
</table>


# Running script
% python .\ExMerge.py -y 2000 -m 1 -Y 2001 -M 2 -i 3 -e foo_bar

Command line options:
<table>
<tr>
<th>-y | --start_year</th>
<th>Extract start year</th>
</tr><tr>
<th>-m | --start_month</th>
<th>Extract start month</th>
</tr><tr>
<th>-Y | --end_year</th>
<th>Extract end year</th>
</tr><tr>
<th>-M | --end_month</th>
<th>Extract end month</th>
</tr><tr>
<th>-i | --interval</th>
<th>Interval of extracts in months</th>
</tr><tr>
<th>-e | --encrypt</th>
<th>Password if encrypting PSTs</th>
</tr>
</table>



# License

BSD 2 Clause. See "LICENSE.txt"
