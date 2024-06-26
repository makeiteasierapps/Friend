import {useContext, useRef, useEffect} from 'react';
import {useNavigation} from '@react-navigation/native';
import {ScrollView, Text, StyleSheet, FlatList} from 'react-native';
import {Button} from 'react-native-elements';
import {GestureHandlerRootView} from 'react-native-gesture-handler';
import {MomentsContext} from '../contexts/MomentsContext';
import useAudioStream from '../hooks/useAudioStream';
import MomentListItem from '../components/moments/MomentsListItem';
import {SafeAreaView} from 'react-native-safe-area-context';

const MomentsTab = () => {
  const {moments} = useContext(MomentsContext);
  
  const {isRecording, displayTranscript, stopRecording, startRecording} =
    useAudioStream();

  const scrollViewRef = useRef(null);
  const navigation = useNavigation();

  useEffect(() => {
    scrollViewRef.current?.scrollToEnd({animated: true});
  }, [displayTranscript]);

  const handleStopRecording = async () => {
    stopRecording();
  };

  const handlePress = momentId => {
    navigation.navigate('Moment Details', {momentId});
  };

  return (
    <GestureHandlerRootView style={{flex: 1}}>
      <SafeAreaView style={styles.container}>
        <Button
          title={isRecording ? 'Stop' : 'Record'}
          onPress={isRecording ? handleStopRecording : startRecording}
          buttonStyle={styles.recordButton}
        />
        <ScrollView ref={scrollViewRef} style={styles.transcriptContainer}>
          <Text style={styles.transcriptText}>{displayTranscript}</Text>
        </ScrollView>
        <FlatList
          data={moments}
          keyExtractor={(item, index) => index.toString()}
          renderItem={({item}) => {
            console.log('Passing momentId:', item.momentId);
            return (
              <MomentListItem momentId={item.momentId} onItemPress={handlePress} />
            );
          }}
          style={{flex: 1}}
        />
      </SafeAreaView>
    </GestureHandlerRootView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
  },

  recordButton: {
    padding: 20,
    margin: 20,
    width: 200,
    alignSelf: 'center',
    backgroundColor: 'red',
    borderRadius: 50,
  },
  buttonText: {
    color: '#FFFFFF',
    fontSize: 20,
  },
  transcriptContainer: {
    height: 200,
    maxHeight: 200,
    margin: 20,
    padding: 10,
    borderWidth: 1,
    borderColor: '#cccccc',
    borderRadius: 5,
    backgroundColor: '#f9f9f9',
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 1},
    shadowOpacity: 0.2,
    shadowRadius: 1.41,
    elevation: 2,
  },

  transcriptText: {
    fontSize: 16,
  },
});

export default MomentsTab;
